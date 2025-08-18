import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './Button'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'Reusable button component with multiple variants, sizes, and loading states.'
      }
    }
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'outline', 'ghost', 'danger']
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg']
    },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' }
  }
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Search'
  }
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Cancel'
  }
}

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Filter'
  }
}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Clear'
  }
}

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Delete'
  }
}

export const Loading: Story = {
  args: {
    variant: 'primary',
    loading: true,
    children: 'Searching...'
  }
}

export const WithIcon: Story = {
  args: {
    variant: 'primary',
    children: (
      <>
        <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
        Search
      </>
    )
  }
}

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  )
}

export const Variants: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="danger">Danger</Button>
    </div>
  )
}