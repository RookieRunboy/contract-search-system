import React, { useState, useCallback, useEffect } from 'react';
import { Button } from 'antd';
import { CloseOutlined } from '@ant-design/icons';
import FilterRow from './FilterRow';
import './FilterBar.css';

// Filter types supported
export type FilterType = 'date' | 'amount' | 'entity' | 'category';

// Value types for different filters
export interface DateFilterValue {
    dateStart?: string;
    dateEnd?: string;
}

export interface AmountFilterValue {
    min?: number;
    max?: number;
}

export interface CategoryFilterValue {
    level1?: string;
    level2?: string[];
}

export type FilterValue = DateFilterValue | AmountFilterValue | CategoryFilterValue | string | string[] | number | null;

// State for a single filter row
export interface FilterRowState {
    id: string;
    type: FilterType | null;
    value: FilterValue;
}

// Props for FilterBar component
interface FilterBarProps {
    categoryHierarchy: Record<string, string[]>;
    entityOptions: string[];
    onFiltersChange: (filters: {
        dateStart?: string;
        dateEnd?: string;
        amountMin?: number;
        amountMax?: number;
        ourEntity?: string;
        customerCategoryLevel1?: string[];
        customerCategoryLevel2?: string[];
    }) => void;
}

// Generate unique ID
const generateId = (): string => {
    return `filter-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const FilterBar: React.FC<FilterBarProps> = ({
    categoryHierarchy,
    entityOptions,
    onFiltersChange
}) => {
    // Initialize with one empty row
    const [rows, setRows] = useState<FilterRowState[]>([
        { id: generateId(), type: null, value: null }
    ]);


    // Convert rows to filter parameters and notify parent
    const convertToFilters = useCallback((currentRows: FilterRowState[]) => {
        const filters: {
            dateStart?: string;
            dateEnd?: string;
            amountMin?: number;
            amountMax?: number;
            ourEntity?: string;
            customerCategoryLevel1?: string[];
            customerCategoryLevel2?: string[];
        } = {};

        currentRows.forEach(row => {
            if (!row.type || row.value === null) return;

            switch (row.type) {
                case 'date':
                    const dateValue = row.value as DateFilterValue;
                    if (dateValue.dateStart) filters.dateStart = dateValue.dateStart;
                    if (dateValue.dateEnd) filters.dateEnd = dateValue.dateEnd;
                    break;
                case 'amount':
                    const amountValue = row.value as AmountFilterValue;
                    if (amountValue.min !== undefined) filters.amountMin = amountValue.min;
                    if (amountValue.max !== undefined) filters.amountMax = amountValue.max;
                    break;
                case 'entity':
                    if (typeof row.value === 'string') filters.ourEntity = row.value;
                    break;
                case 'category':
                    const catValue = row.value as CategoryFilterValue;
                    if (catValue.level1) {
                        if (!filters.customerCategoryLevel1) {
                            filters.customerCategoryLevel1 = [];
                        }
                        if (!filters.customerCategoryLevel1.includes(catValue.level1)) {
                            filters.customerCategoryLevel1.push(catValue.level1);
                        }
                        // Only add level2 if specific selections are made (not empty = all)
                        if (catValue.level2 && catValue.level2.length > 0) {
                            if (!filters.customerCategoryLevel2) {
                                filters.customerCategoryLevel2 = [];
                            }
                            catValue.level2.forEach(l2 => {
                                if (!filters.customerCategoryLevel2!.includes(l2)) {
                                    filters.customerCategoryLevel2!.push(l2);
                                }
                            });
                        }
                    }
                    break;

            }
        });

        return filters;
    }, []);

    // Update parent when rows change
    useEffect(() => {
        const filters = convertToFilters(rows);
        onFiltersChange(filters);
    }, [rows, convertToFilters, onFiltersChange]);

    // Handle type change for a row
    const handleTypeChange = useCallback((id: string, type: FilterType | null) => {
        setRows(prev => {
            const newRows = prev.map(row => {
                if (row.id === id) {
                    // Reset value when type changes
                    let defaultValue: FilterValue = null;
                    if (type === 'date' || type === 'amount') {
                        defaultValue = {};
                    } else if (type === 'category') {
                        defaultValue = { level1: undefined, level2: [] };
                    }
                    return { ...row, type, value: defaultValue };
                }
                return row;
            });

            // If the modified row was the last empty row and now has a type,
            // add a new empty row at the bottom
            const lastRow = newRows[newRows.length - 1];
            if (lastRow && lastRow.type !== null) {
                newRows.push({ id: generateId(), type: null, value: null });
            }

            return newRows;
        });
    }, []);

    // Handle value change for a row
    const handleValueChange = useCallback((id: string, value: FilterValue) => {
        setRows(prev => {
            const newRows = prev.map(row => {
                if (row.id === id) {
                    return { ...row, value };
                }
                return row;
            });
            return newRows;
        });
    }, []);

    // Handle remove row
    const handleRemove = useCallback((id: string) => {
        setRows(prev => {
            // Don't remove if it's the only row
            if (prev.length === 1) {
                return [{ id: generateId(), type: null, value: null }];
            }

            const newRows = prev.filter(row => row.id !== id);

            // Ensure at least one empty row exists at the bottom
            const lastRow = newRows[newRows.length - 1];
            if (lastRow && lastRow.type !== null) {
                newRows.push({ id: generateId(), type: null, value: null });
            }

            return newRows;
        });
    }, []);

    // Handle clear all
    const handleClearAll = useCallback(() => {
        setRows([{ id: generateId(), type: null, value: null }]);
    }, []);

    // Get used filter types (to disable in other rows)
    // Note: 'category' type can be used multiple times to support multiple level1 selections
    const usedTypes = rows
        .filter(row => row.type !== null && row.type !== 'category')
        .map(row => row.type as FilterType);

    // Check if there are any active filters
    const hasActiveFilters = rows.some(row => row.type !== null);

    return (
        <div className="filter-bar">
            <div className="filter-bar-rows">
                {rows.map((row, index) => (
                    <FilterRow
                        key={row.id}
                        id={row.id}
                        type={row.type}
                        value={row.value}
                        onTypeChange={handleTypeChange}
                        onValueChange={handleValueChange}
                        onRemove={handleRemove}
                        usedTypes={usedTypes}
                        categoryHierarchy={categoryHierarchy}
                        entityOptions={entityOptions}
                        isLastRow={index === rows.length - 1 && row.type === null}
                    />
                ))}
            </div>

            {hasActiveFilters && (
                <div className="filter-bar-footer">
                    <Button
                        type="text"
                        size="small"
                        icon={<CloseOutlined />}
                        onClick={handleClearAll}
                        className="clear-all-button"
                    >
                        清除筛选
                    </Button>
                </div>
            )}
        </div>
    );
};

export default FilterBar;
