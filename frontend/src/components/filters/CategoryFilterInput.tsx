import React from 'react';
import { Select } from 'antd';
import '../FilterBar.css';

interface CategoryFilterInputProps {
    value: string[];
    options: string[];
    onChange: (value: string[]) => void;
    placeholder?: string;
    disabled?: boolean;
}

const CategoryFilterInput: React.FC<CategoryFilterInputProps> = ({
    value,
    options,
    onChange,
    placeholder = '选择分类',
    disabled = false
}) => {
    return (
        <Select
            mode="multiple"
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            className="category-filter-select"
            disabled={disabled}
            allowClear
            showSearch
            options={options.map(opt => ({ label: opt, value: opt }))}
            filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            maxTagCount="responsive"
        />
    );
};

export default CategoryFilterInput;
