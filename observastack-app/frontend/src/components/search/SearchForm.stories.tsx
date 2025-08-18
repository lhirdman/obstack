import type { Meta, StoryObj } from '@storybook/react'
import { SearchForm } from './SearchForm'
import { SearchQuery } from '../../types'

const meta: Meta<typeof SearchForm> = {
  title: 'Search/SearchForm',
  component: SearchForm,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Advanced search form with filters, time range selection, and cross-signal search capabilities.'
      }
    }
  },
  argTypes: {
    onSearch: { action: 'search' },
    loading: { control: 'boolean' },
    initialQuery: { control: 'object' }
  }
}

export default meta
type Story = StoryObj<typeof SearchForm>

export const Default: Story = {
  args: {
    loading: false
  }
}

export const Loading: Story = {
  args: {
    loading: true
  }
}

export const WithInitialQuery: Story = {
  args: {
    loading: false,
    initialQuery: {
      freeText: 'error rate',
      type: 'logs',
      timeRange: {
        from: 'now-1h',
        to: 'now'
      },
      filters: [
        {
          field: 'level',
          operator: 'equals',
          value: 'error'
        }
      ]
    }
  }
}

export const WithFilters: Story = {
  args: {
    loading: false,
    initialQuery: {
      freeText: 'authentication',
      type: 'all',
      timeRange: {
        from: 'now-24h',
        to: 'now'
      },
      filters: [
        {
          field: 'service',
          operator: 'equals',
          value: 'auth-service'
        },
        {
          field: 'status',
          operator: 'range',
          value: [400, 500]
        }
      ]
    }
  }
}