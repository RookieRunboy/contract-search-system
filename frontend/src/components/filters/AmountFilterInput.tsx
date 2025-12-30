import React from 'react';
import { InputNumber } from 'antd';
import type { AmountFilterValue } from '../FilterBar';
import '../FilterBar.css';

interface AmountFilterInputProps {
    value: AmountFilterValue;
    onChange: (value: AmountFilterValue) => void;
}

const AmountFilterInput: React.FC<AmountFilterInputProps> = ({ value, onChange }) => {
    const handleMinChange = (min: number | null) => {
        onChange({
            ...value,
            min: min ?? undefined
        });
    };

    const handleMaxChange = (max: number | null) => {
        onChange({
            ...value,
            max: max ?? undefined
        });
    };

    return (
        <div className="amount-filter-input">
            <InputNumber
                value={value?.min}
                onChange={handleMinChange}
                placeholder="最小金额"
                min={0}
                className="amount-input-min"
                formatter={val => `${val}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={val => parseFloat(val!.replace(/\$\s?|(,*)/g, '')) || 0}
            />
            <span className="amount-separator">-</span>
            <InputNumber
                value={value?.max}
                onChange={handleMaxChange}
                placeholder="最大金额"
                min={0}
                className="amount-input-max"
                formatter={val => `${val}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={val => parseFloat(val!.replace(/\$\s?|(,*)/g, '')) || 0}
            />
        </div>
    );
};

export default AmountFilterInput;
