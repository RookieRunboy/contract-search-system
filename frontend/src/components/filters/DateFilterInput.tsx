import React from 'react';
import { DatePicker } from 'antd';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import type { DateFilterValue } from '../FilterBar';
import '../FilterBar.css';

interface DateFilterInputProps {
    value: DateFilterValue;
    onChange: (value: DateFilterValue) => void;
}

const DateFilterInput: React.FC<DateFilterInputProps> = ({ value, onChange }) => {
    const handleStartChange = (date: Dayjs | null) => {
        onChange({
            ...value,
            dateStart: date ? date.format('YYYY-MM-DD') : undefined
        });
    };

    const handleEndChange = (date: Dayjs | null) => {
        onChange({
            ...value,
            dateEnd: date ? date.format('YYYY-MM-DD') : undefined
        });
    };

    const startValue = value?.dateStart ? dayjs(value.dateStart) : null;
    const endValue = value?.dateEnd ? dayjs(value.dateEnd) : null;

    return (
        <div className="date-filter-input">
            <DatePicker
                value={startValue}
                onChange={handleStartChange}
                placeholder="开始日期"
                format="YYYY-MM-DD"
                className="date-picker-start"
                allowClear
            />
            <span className="date-separator">→</span>
            <DatePicker
                value={endValue}
                onChange={handleEndChange}
                placeholder="结束日期"
                format="YYYY-MM-DD"
                className="date-picker-end"
                allowClear
            />
        </div>
    );
};

export default DateFilterInput;
