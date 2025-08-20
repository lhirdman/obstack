import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the main heading', () => {
    render(<App />);
    
    const heading = screen.getByRole('heading', { name: /observastack frontend/i });
    expect(heading).toBeInTheDocument();
  });

  it('renders the ready message', () => {
    render(<App />);
    
    const message = screen.getByText(/ready for development/i);
    expect(message).toBeInTheDocument();
  });
});