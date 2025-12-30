import React, { useCallback, useMemo } from 'react';
import { Select } from 'antd';
import '../FilterBar.css';

export interface CategoryFilterValue {
    level1?: string;
    level2?: string[];
}

interface HierarchicalCategoryFilterProps {
    value: CategoryFilterValue;
    categoryHierarchy: Record<string, string[]>;
    onChange: (value: CategoryFilterValue) => void;
}

const HierarchicalCategoryFilter: React.FC<HierarchicalCategoryFilterProps> = ({
    value,
    categoryHierarchy,
    onChange
}) => {
    // Get level1 options from category hierarchy keys
    const level1Options = useMemo(() => {
        return Object.keys(categoryHierarchy).map(cat => ({
            label: cat,
            value: cat
        }));
    }, [categoryHierarchy]);

    // Get level2 options based on selected level1
    const level2Options = useMemo(() => {
        if (!value.level1 || !categoryHierarchy[value.level1]) {
            return [];
        }
        return categoryHierarchy[value.level1].map(cat => ({
            label: cat,
            value: cat
        }));
    }, [value.level1, categoryHierarchy]);

    // Handle level1 change
    const handleLevel1Change = useCallback((newLevel1: string | undefined) => {
        onChange({
            level1: newLevel1,
            level2: [] // Reset level2 when level1 changes
        });
    }, [onChange]);

    // Handle level2 change
    const handleLevel2Change = useCallback((newLevel2: string[]) => {
        onChange({
            ...value,
            level2: newLevel2
        });
    }, [value, onChange]);

    // Handle clear level1
    const handleLevel1Clear = useCallback(() => {
        onChange({
            level1: undefined,
            level2: []
        });
    }, [onChange]);

    return (
        <div className="hierarchical-category-filter">
            <Select
                value={value.level1}
                onChange={handleLevel1Change}
                onClear={handleLevel1Clear}
                placeholder="选择一级分类"
                className="category-level1-select"
                allowClear
                showSearch
                options={level1Options}
                filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
            />
            <Select
                mode="multiple"
                value={value.level2 || []}
                onChange={handleLevel2Change}
                placeholder={value.level1 ? "全部" : "请先选择一级分类"}
                className="category-level2-select"
                disabled={!value.level1}
                allowClear
                showSearch
                options={level2Options}
                filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                maxTagCount="responsive"
            />
        </div>
    );
};

export default HierarchicalCategoryFilter;
