"""
Keycloak integration service for OIDC authentication and JWT validation.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import requests
from jose import JWTError, jwt
from jose.constants import ALGORITHMS

from app.core.config import settings

logger = logging.getLogger(__name__)


class KeycloakService:
    """Service for Keycloak OIDC integration and JWT validation."""
    
    def __init__(self):
        self._jwks_cache: Optional[Dict] = None
        self._realm_info_cache: Optional[Dict] = None
        
    @property
    def realm_url(self) -> str:
        """Get the Keycloak realm URL."""
        return urljoin(settings.keycloak_server_url, f"/realms/{settings.keycloak_realm}")
    
    @property
    def jwks_uri(self) -> str:
        """Get the JWKS URI for the realm."""
        return urljoin(self.realm_url, "/protocol/openid_connect/certs")
    
    @property
    def realm_info_uri(self) -> str:
        """Get the realm info URI."""
        return self.realm_url
    
    def get_realm_info(self) -> Dict[str, Any]:
        """
        Get realm information from Keycloak.
        
        Returns:
            Dict containing realm configuration
            
        Raises:
            requests.RequestException: If unable to fetch realm info
        """
        if self._realm_info_cache is None:
            try:
                response = requests.get(self.realm_info_uri, timeout=10)
                response.raise_for_status()
                self._realm_info_cache = response.json()
                logger.info(f"Fetched realm info for {settings.keycloak_realm}")
            except requests.RequestException as e:
                logger.error(f"Failed to fetch realm info: {e}")
                raise
        
        return self._realm_info_cache
    
    def get_jwks(self) -> Dict[str, Any]:
        """
        Get JSON Web Key Set (JWKS) from Keycloak.
        
        Returns:
            Dict containing JWKS data
            
        Raises:
            requests.RequestException: If unable to fetch JWKS
        """
        if self._jwks_cache is None:
            try:
                response = requests.get(self.jwks_uri, timeout=10)
                response.raise_for_status()
                self._jwks_cache = response.json()
                logger.info(f"Fetched JWKS from {self.jwks_uri}")
            except requests.RequestException as e:
                logger.error(f"Failed to fetch JWKS: {e}")
                raise
        
        return self._jwks_cache
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a JWT token issued by Keycloak.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict containing token payload if valid, None if invalid
        """
        try:
            # Get JWKS for token validation
            jwks = self.get_jwks()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                logger.warning("JWT token missing key ID (kid)")
                return None
            
            # Find the matching key in JWKS
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
            
            if not key:
                logger.warning(f"No matching key found for kid: {kid}")
                return None
            
            # Get realm info for issuer validation
            realm_info = self.get_realm_info()
            expected_issuer = realm_info.get("issuer")
            
            # Validate and decode the token
            payload = jwt.decode(
                token,
                key,
                algorithms=[ALGORITHMS.RS256],
                audience=settings.keycloak_client_id,
                issuer=expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                }
            )
            
            logger.debug(f"Successfully validated JWT for user: {payload.get('preferred_username')}")
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during JWT validation: {e}")
            return None
    
    def extract_user_info(self, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from Keycloak JWT payload.
        
        Args:
            token_payload: Decoded JWT payload
            
        Returns:
            Dict containing extracted user information
        """
        return {
            "user_id": token_payload.get("sub"),
            "username": token_payload.get("preferred_username"),
            "email": token_payload.get("email"),
            "first_name": token_payload.get("given_name"),
            "last_name": token_payload.get("family_name"),
            "full_name": token_payload.get("name"),
            "email_verified": token_payload.get("email_verified", False),
        }
    
    def extract_roles(self, token_payload: Dict[str, Any]) -> List[str]:
        """
        Extract roles from Keycloak JWT payload.
        
        Args:
            token_payload: Decoded JWT payload
            
        Returns:
            List of role names
        """
        roles = []
        
        # Extract realm roles
        realm_access = token_payload.get("realm_access", {})
        realm_roles = realm_access.get("roles", [])
        roles.extend(realm_roles)
        
        # Extract client roles
        resource_access = token_payload.get("resource_access", {})
        client_access = resource_access.get(settings.keycloak_client_id, {})
        client_roles = client_access.get("roles", [])
        roles.extend([f"client:{role}" for role in client_roles])
        
        # Remove system roles that shouldn't be exposed
        system_roles = {"offline_access", "uma_authorization", "default-roles-*"}
        filtered_roles = [role for role in roles if not any(role.startswith(sys_role.replace("*", "")) for sys_role in system_roles)]
        
        return filtered_roles
    
    def extract_tenant_info(self, token_payload: Dict[str, Any]) -> Optional[str]:
        """
        Extract tenant information from Keycloak JWT payload.
        
        Args:
            token_payload: Decoded JWT payload
            
        Returns:
            Tenant identifier or None if not found
        """
        # Try different common claim names for tenant/organization
        tenant_claims = ["tenant", "organization", "org", "company", "tenant_id", "org_id"]
        
        for claim in tenant_claims:
            tenant = token_payload.get(claim)
            if tenant:
                return str(tenant)
        
        # Fallback: use realm name as tenant if no specific tenant claim
        return settings.keycloak_realm
    
    def map_keycloak_roles_to_internal(self, keycloak_roles: List[str]) -> List[str]:
        """
        Map Keycloak roles to internal application roles.
        
        Args:
            keycloak_roles: List of Keycloak role names
            
        Returns:
            List of internal application role names
        """
        # Define role mapping - this can be made configurable later
        role_mapping = {
            # Admin roles
            "admin": "admin",
            "realm-admin": "admin",
            "client:admin": "admin",
            
            # Manager roles
            "manager": "manager",
            "team-lead": "manager",
            "client:manager": "manager",
            
            # User roles
            "user": "user",
            "member": "user",
            "client:user": "user",
            
            # Viewer roles
            "viewer": "viewer",
            "read-only": "viewer",
            "client:viewer": "viewer",
        }
        
        internal_roles = set()
        
        for keycloak_role in keycloak_roles:
            # Direct mapping
            if keycloak_role in role_mapping:
                internal_roles.add(role_mapping[keycloak_role])
            # Pattern matching for client roles
            elif keycloak_role.startswith("client:"):
                base_role = keycloak_role.replace("client:", "")
                if base_role in role_mapping:
                    internal_roles.add(role_mapping[base_role])
        
        # Ensure at least 'user' role if no other roles mapped
        if not internal_roles:
            internal_roles.add("user")
        
        return list(internal_roles)
    
    def clear_cache(self):
        """Clear cached JWKS and realm info."""
        self._jwks_cache = None
        self._realm_info_cache = None
        logger.info("Cleared Keycloak service cache")


# Global service instance
keycloak_service = KeycloakService()