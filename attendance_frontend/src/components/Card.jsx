import React from 'react';

const Card = ({ title, children }) => (
  <div className="card">
    <h2 className="text-xl font-semibold text-primary mb-4">{title}</h2>
    {children}
  </div>
);

export default Card;