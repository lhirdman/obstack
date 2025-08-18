import type { Meta, StoryObj } from '@storybook/react'
import { SearchHistory } from './SearchHistory'

const meta: Meta<typeof SearchHistory> = {
  title: 'Search/SearchHistory',
  component: SearchHistory,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: 'Search history and saved searches management with quick access to previous queries.'
      }
    }
  },
  argTypes: {
    onSelectQuery: { action: 'select-query' },
    onSaveQuery: { action: 'save-query' },
    onDeleteQuery: { action: 'delete-query' }
  }
}

export default meta
type Story = StoryObj<typeof SearchHistory>

export const Default: Story = {
  args: {}
}

export const WithActions: Story = {
  args: {
    onSaveQuery: async (item, name) => {
      console.log('Saving query:', item, 'with name:', name)
    },
    onDeleteQuery: async (id) => {
      console.log('Deleting query:', id)
    }
  }
}