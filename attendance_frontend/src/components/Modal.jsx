// src/components/Modal.jsx
const Modal = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-soft w-full max-w-md">
        {children}
        <button onClick={onClose} className="mt-4 bg-accent text-white px-4 py-2 rounded hover:bg-primary transition-colors">
          Close
        </button>
      </div>
    </div>
  );
};

export default Modal;