import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Grid, GridItem } from './Grid'

describe('Grid', () => {
  it('renders with default props', () => {
    render(
      <Grid data-testid="grid">
        <div>Item 1</div>
        <div>Item 2</div>
      </Grid>
    )

    const grid = screen.getByTestId('grid')
    expect(grid).toHaveClass('grid', 'grid-cols-1', 'gap-4')
  })

  it('applies custom columns and gap', () => {
    render(
      <Grid cols={3} gap="lg" data-testid="grid">
        <div>Item 1</div>
        <div>Item 2</div>
        <div>Item 3</div>
      </Grid>
    )

    const grid = screen.getByTestId('grid')
    expect(grid).toHaveClass('grid-cols-3', 'gap-6')
  })

  it('applies responsive classes', () => {
    render(
      <Grid
        cols={1}
        responsive={{ sm: 2, md: 3, lg: 4 }}
        data-testid="grid"
      >
        <div>Item 1</div>
        <div>Item 2</div>
      </Grid>
    )

    const grid = screen.getByTestId('grid')
    expect(grid).toHaveClass('grid-cols-1', 'sm:grid-cols-2', 'md:grid-cols-3', 'lg:grid-cols-4')
  })

  it('applies custom className', () => {
    render(
      <Grid className="custom-class" data-testid="grid">
        <div>Item</div>
      </Grid>
    )

    const grid = screen.getByTestId('grid')
    expect(grid).toHaveClass('custom-class')
  })
})

describe('GridItem', () => {
  it('renders with default span', () => {
    render(
      <GridItem data-testid="grid-item">
        Content
      </GridItem>
    )

    const item = screen.getByTestId('grid-item')
    expect(item).toHaveClass('col-span-1')
  })

  it('applies custom span', () => {
    render(
      <GridItem span={6} data-testid="grid-item">
        Content
      </GridItem>
    )

    const item = screen.getByTestId('grid-item')
    expect(item).toHaveClass('col-span-6')
  })

  it('applies responsive span classes', () => {
    render(
      <GridItem
        span={1}
        responsive={{ sm: 2, md: 4, lg: 6 }}
        data-testid="grid-item"
      >
        Content
      </GridItem>
    )

    const item = screen.getByTestId('grid-item')
    expect(item).toHaveClass('col-span-1', 'sm:col-span-2', 'md:col-span-4', 'lg:col-span-6')
  })
})