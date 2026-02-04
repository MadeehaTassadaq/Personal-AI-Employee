# UI/UX Patterns & Interactive Components Guide

## Modern UI Components

### Animated Modal
```jsx
'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef } from 'react';

export function AnimatedModal({ isOpen, onClose, children }) {
  const modalRef = useRef();

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            ref={modalRef}
            className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Smooth Page Transitions
```jsx
// app/layout.js
import { motion } from 'framer-motion';
import { usePathname } from 'next/navigation';

function AppWrapper({ children }) {
  const pathname = usePathname();

  return (
    <motion.div
      key={pathname}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}
```

### Interactive Cards
```jsx
'use client';

import { motion } from 'framer-motion';

export function InteractiveCard({ children, href, ...props }) {
  return (
    <motion.div
      whileHover={{ y: -5, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className="bg-white rounded-xl shadow-lg overflow-hidden cursor-pointer"
      {...props}
    >
      {children}
    </motion.div>
  );
}
```

## Form Patterns

### Multi-step Form
```jsx
'use client';

import { useState } from 'react';

export function MultiStepForm() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({});

  const nextStep = () => setStep(step + 1);
  const prevStep = () => setStep(step - 1);

  const updateFormData = (data) => {
    setFormData({ ...formData, ...data });
  };

  return (
    <div className="max-w-md mx-auto">
      {step === 1 && (
        <StepOne data={formData} updateData={updateFormData} nextStep={nextStep} />
      )}
      {step === 2 && (
        <StepTwo data={formData} updateData={updateFormData} nextStep={nextStep} prevStep={prevStep} />
      )}
      {step === 3 && (
        <StepThree data={formData} updateData={updateFormData} />
      )}

      <div className="flex justify-between mt-6">
        {step > 1 && (
          <button onClick={prevStep} className="px-4 py-2 bg-gray-200 rounded">
            Previous
          </button>
        )}
        {step < 3 && (
          <button onClick={nextStep} className="px-4 py-2 bg-blue-500 text-white rounded ml-auto">
            Next
          </button>
        )}
      </div>
    </div>
  );
}
```

### Animated Input Fields
```jsx
'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';

export function AnimatedInput({ label, type = 'text', ...props }) {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className="relative">
      <input
        type={type}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        className="w-full p-3 border-b-2 border-gray-300 focus:border-blue-500 outline-none transition-colors duration-300"
        {...props}
      />
      <motion.label
        animate={{
          y: isFocused || props.value ? -20 : 0,
          scale: isFocused || props.value ? 0.8 : 1,
        }}
        className="absolute left-0 top-3 text-gray-500 transition-all duration-300"
      >
        {label}
      </motion.label>
    </div>
  );
}
```

## Navigation Patterns

### Animated Navigation
```jsx
'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';

export function AnimatedNav() {
  const [activeIndex, setActiveIndex] = useState(0);
  const navItems = ['Home', 'About', 'Services', 'Contact'];

  return (
    <nav className="flex space-x-8">
      {navItems.map((item, index) => (
        <Link href={`/${item.toLowerCase()}`} key={item}>
          <motion.div
            className="relative cursor-pointer py-2 px-1"
            onMouseEnter={() => setActiveIndex(index)}
            whileHover={{ scale: 1.05 }}
          >
            {item}
            {activeIndex === index && (
              <motion.div
                layoutId="navIndicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </motion.div>
        </Link>
      ))}
    </nav>
  );
}
```

## Data Visualization

### Animated Progress Bar
```jsx
'use client';

import { motion } from 'framer-motion';

export function AnimatedProgressBar({ value, max = 100 }) {
  const percentage = (value / max) * 100;

  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <motion.div
        className="bg-blue-600 h-2.5 rounded-full"
        initial={{ width: 0 }}
        animate={{ width: `${percentage}%` }}
        transition={{ duration: 1, ease: 'easeOut' }}
      />
    </div>
  );
}
```

### Interactive Data Table
```jsx
'use client';

import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

export function InteractiveTable({ data, columns }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [filterText, setFilterText] = useState('');

  const filteredData = useMemo(() => {
    return data.filter(item =>
      Object.values(item).some(value =>
        value.toString().toLowerCase().includes(filterText.toLowerCase())
      )
    );
  }, [data, filterText]);

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return filteredData;

    return [...filteredData].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [filteredData, sortConfig]);

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Filter..."
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
        className="mb-4 p-2 border rounded"
      />
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer"
                onClick={() => handleSort(column.key)}
              >
                {column.label}
                {sortConfig.key === column.key && (
                  <span>{sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {sortedData.map((item, index) => (
            <motion.tr
              key={item.id || index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ backgroundColor: '#f3f4f6' }}
              className="hover:bg-gray-50"
            >
              {columns.map((column) => (
                <td key={column.key} className="px-6 py-4 whitespace-nowrap">
                  {column.render ? column.render(item[column.key], item) : item[column.key]}
                </td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

## Responsive Design Patterns

### Responsive Grid
```jsx
// components/ResponsiveGrid.jsx
import { motion } from 'framer-motion';

export function ResponsiveGrid({ items, itemComponent: ItemComponent }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {items.map((item, index) => (
        <motion.div
          key={item.id || index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <ItemComponent item={item} />
        </motion.div>
      ))}
    </div>
  );
}
```

### Mobile-First Navigation
```jsx
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const navItems = ['Home', 'About', 'Services', 'Contact'];

  return (
    <nav className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2"
        aria-label="Toggle navigation"
      >
        <div className="w-6 h-0.5 bg-black mb-1.5"></div>
        <div className="w-6 h-0.5 bg-black mb-1.5"></div>
        <div className="w-6 h-0.5 bg-black"></div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="absolute top-full left-0 right-0 bg-white shadow-lg rounded-b-lg overflow-hidden"
          >
            <ul className="py-2">
              {navItems.map((item) => (
                <li key={item}>
                  <a
                    href={`/${item.toLowerCase()}`}
                    className="block px-4 py-2 hover:bg-gray-100"
                    onClick={() => setIsOpen(false)}
                  >
                    {item}
                  </a>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
```

## Accessibility Patterns

### Skip Navigation Link
```jsx
// components/SkipNavigation.jsx
export function SkipNavigation() {
  return (
    <a
      href="#main-content"
      className="absolute -top-20 left-4 bg-white p-2 border rounded shadow-md focus:top-4 transition-all duration-300 z-50"
    >
      Skip to main content
    </a>
  );
}
```

### Focus Visible
```jsx
// globals.css
.focus-visible {
  outline: 2px solid #3B82F6;
  outline-offset: 2px;
}

// Component using focus visible
export function FocusVisibleButton({ children, ...props }) {
  return (
    <button
      className="focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 focus-visible:outline-offset-2 rounded"
      {...props}
    >
      {children}
    </button>
  );
}
```

## Performance Patterns

### Virtual Scrolling (Concept)
```jsx
// For large lists, consider using react-window or similar
import { FixedSizeList as List } from 'react-window';

const VirtualizedList = ({ items }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      {items[index].name}
    </div>
  );

  return (
    <List
      height={400}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

### Lazy Loading Images
```jsx
import { useInView } from 'react-intersection-observer';
import { useState } from 'react';

export function LazyImage({ src, alt, ...props }) {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });
  const [loaded, setLoaded] = useState(false);

  return (
    <div ref={ref}>
      {inView && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          className={`transition-opacity duration-300 ${loaded ? 'opacity-100' : 'opacity-0'}`}
          {...props}
        />
      )}
    </div>
  );
}
```

## Animation Best Practices

### Staggered Animations
```jsx
import { motion } from 'framer-motion';

export function StaggeredList({ items }) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: 0.1,
          },
        },
      }}
    >
      {items.map((item) => (
        <motion.div
          key={item.id}
          variants={{
            hidden: { y: 20, opacity: 0 },
            visible: { y: 0, opacity: 1 },
          }}
          className="p-4 border-b"
        >
          {item.name}
        </motion.div>
      ))}
    </motion.div>
  );
}
```

### Scroll-Based Animations
```jsx
'use client';

import { useEffect, useRef } from 'react';
import { motion, useInView, useAnimation } from 'framer-motion';

export function ScrollAnimation({ children, ...props }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const controls = useAnimation();

  useEffect(() => {
    if (isInView) {
      controls.start('visible');
    }
  }, [controls, isInView]);

  return (
    <motion.div
      ref={ref}
      animate={controls}
      initial="hidden"
      variants={{
        hidden: { opacity: 0, y: 50 },
        visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
```