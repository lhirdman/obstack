import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchFilters } from './SearchFilters'
import { SearchFilter } from '../../types'

describe('SearchFilters', () => {
  const mockOnFiltersChange = vi.fn()
  const mockOnClose = vi.fn()

  const defaultFilters: SearchFilter[] = [
    { field: 'level', operator: 'equals', value: 'error' },
    { field: 'service', operator: 'contains', value: 'api' }
  ]

  beforeEach(() => {
    mockOnFiltersChange.mockClear()
    mockOnClose.mockClear()
  })

  it('renders with default state', () => {
    render(
      <SearchFilters
        filters={[]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByText('Search Filters')).toBeInTheDocument()
    expect(screen.getByText('Add Filter')).toBeInTheDocument()
    expect(screen.getByText('Clear All')).toBeInTheDocument()
  })

  it('displays existing filters', () => {
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    expect(screen.getByDisplayValue('level')).toBeInTheDocument()
    expect(screen.getByDisplayValue('error')).toBeInTheDocument()
    expect(screen.getByDisplayValue('service')).toBeInTheDocument()
    expect(screen.getByDisplayValue('api')).toBeInTheDocument()
  })

  it('adds new filter when Add Filter is clicked', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={[]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const addButton = screen.getByText('Add Filter')
    await user.click(addButton)

    expect(mockOnFiltersChange).toHaveBeenCalledWith([
      { field: '', operator: 'equals', value: '' }
    ])
  })

  it('removes filter when remove button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const removeButtons = screen.getAllByLabelText('Remove filter')
    await user.click(removeButtons[0])

    expect(mockOnFiltersChange).toHaveBeenCalledWith([
      { field: 'service', operator: 'contains', value: 'api' }
    ])
  })

  it('clears all filters when Clear All is clicked', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const clearButton = screen.getByText('Clear All')
    await user.click(clearButton)

    expect(mockOnFiltersChange).toHaveBeenCalledWith([])
  })

  it('updates filter field when changed', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={[{ field: 'level', operator: 'equals', value: 'error' }]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const fieldSelect = screen.getByDisplayValue('level')
    await user.selectOptions(fieldSelect, 'service')

    expect(mockOnFiltersChange).toHaveBeenCalledWith([
      { field: 'service', operator: 'equals', value: 'error' }
    ])
  })

  it('updates filter operator when changed', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={[{ field: 'level', operator: 'equals', value: 'error' }]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const operatorSelect = screen.getByDisplayValue('equals')
    await user.selectOptions(operatorSelect, 'contains')

    expect(mockOnFiltersChange).toHaveBeenCalledWith([
      { field: 'level', operator: 'contains', value: 'error' }
    ])
  })

  it('updates filter value when changed', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={[{ field: 'level', operator: 'equals', value: 'error' }]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const valueInput = screen.getByDisplayValue('error')
    await user.clear(valueInput)
    await user.type(valueInput, 'warning')

    expect(mockOnFiltersChange).toHaveBeenCalledWith([
      { field: 'level', operator: 'equals', value: 'warning' }
    ])
  })

  it('closes when close button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <SearchFilters
        filters={[]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const closeButton = screen.getByLabelText('Close filters')
    await user.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('shows available field options', () => {
    render(
      <SearchFilters
        filters={[{ field: '', operator: 'equals', value: '' }]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const fieldSelect = screen.getByDisplayValue('')
    expect(fieldSelect).toBeInTheDocument()
    
    // Check that common field options are available
    const options = screen.getAllByRole('option')
    const optionTexts = options.map(option => option.textContent)
    expect(optionTexts).toContain('level')
    expect(optionTexts).toContain('service')
    expect(optionTexts).toContain('message')
  })

  it('shows available operator options', () => {
    render(
      <SearchFilters
        filters={[{ field: 'level', operator: 'equals', value: '' }]}
        onFiltersChange={mockOnFiltersChange}
        onClose={mockOnClose}
      />
    )

    const operatorSelect = screen.getByDisplayValue('equals')
    expect(operatorSelect).toBeInTheDocument()
    
    // Check that operator options are available
    const options = screen.getAllByRole('option')
    const optionTexts = options.map(option => option.textContent)
    expect(optionTexts).toContain('equals')
    expect(optionTexts).toContain('contains')
    expect(optionTexts).toContain('not equals')
  })
})