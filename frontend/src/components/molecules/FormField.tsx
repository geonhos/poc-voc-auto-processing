/**
 * Form Field Component - Presentational
 */

import './FormField.css';

interface FormFieldProps {
  label: string;
  required?: boolean;
  error?: string;
  children: React.ReactNode;
  htmlFor?: string;
}

export const FormField = ({
  label,
  required = false,
  error,
  children,
  htmlFor,
}: FormFieldProps) => {
  return (
    <div className="form-field">
      <label htmlFor={htmlFor} className={required ? 'required' : ''}>
        {label}
      </label>
      {children}
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};
