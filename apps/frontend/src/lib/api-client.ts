/**
 * API client utility that automatically includes credentials for authenticated requests.
 * This ensures that HttpOnly cookies are sent with all API calls.
 */

interface ApiClientOptions extends RequestInit {
  baseUrl?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: ApiClientOptions = {}
  ): Promise<T> {
    const { baseUrl, ...requestOptions } = options;
    const url = `${baseUrl || this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...requestOptions.headers,
      },
      credentials: 'include', // Always include cookies for authentication
      ...requestOptions,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    // Handle empty responses (like 204 No Content)
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }
    
    return response.text() as unknown as T;
  }

  // HTTP method helpers
  async get<T>(endpoint: string, options?: ApiClientOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  async post<T>(
    endpoint: string,
    data?: any,
    options?: ApiClientOptions
  ): Promise<T> {
    const config: ApiClientOptions = {
      ...options,
      method: 'POST',
    };
    
    if (data) {
      config.body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, config);
  }

  async put<T>(
    endpoint: string,
    data?: any,
    options?: ApiClientOptions
  ): Promise<T> {
    const config: ApiClientOptions = {
      ...options,
      method: 'PUT',
    };
    
    if (data) {
      config.body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, config);
  }

  async patch<T>(
    endpoint: string,
    data?: any,
    options?: ApiClientOptions
  ): Promise<T> {
    const config: ApiClientOptions = {
      ...options,
      method: 'PATCH',
    };
    
    if (data) {
      config.body = JSON.stringify(data);
    }
    
    return this.request<T>(endpoint, config);
  }

  async delete<T>(endpoint: string, options?: ApiClientOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

// Export a default instance
export const apiClient = new ApiClient();

// Export the class for custom instances
export default ApiClient;