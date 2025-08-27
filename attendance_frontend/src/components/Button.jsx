import React from 'react';

const Button = ({ children, onClick, variant = 'primary', className = '' }) => {
  const baseStyles = 'px-4 py-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  const variantStyles = variant === 'primary' ? 'bg-primary text-white hover:bg-blue-700 focus:ring-blue-500' : 'bg-accent text-white hover:bg-amber-600 focus:ring-amber-500';
  return (
    <button onClick={onClick} className={`${baseStyles} ${variantStyles} ${className}`}>
      {children}
    </button>
  );
};

export default Button;