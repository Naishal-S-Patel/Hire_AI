import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Mail, Phone, MapPin, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';

const BasicDetailsForm = ({ onSubmit, initialEmail, disabled }) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState(initialEmail || '');
  const [mobile, setMobile] = useState('');
  const [residence, setResidence] = useState('');
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [touched, setTouched] = useState({});

  // Real-time validation
  const validateField = (name, value) => {
    switch (name) {
      case 'firstName':
      case 'lastName':
        if (!value.trim()) return 'This field is required';
        if (value.length < 2) return 'Must be at least 2 characters';
        if (value.length > 50) return 'Must be less than 50 characters';
        if (!/^[a-zA-Z\s'-]+$/.test(value)) return 'Only letters, spaces, hyphens and apostrophes allowed';
        return '';
      case 'email':
        if (!value.trim()) return 'Email is required';
        if (!/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(value)) return 'Invalid email format';
        return '';
      case 'mobile':
        if (!value.trim()) return 'Mobile number is required';
        const cleaned = value.replace(/[\s\-\(\)]/g, '');
        if (!/^\+?[\d]{8,15}$/.test(cleaned)) return 'Invalid phone number (8-15 digits)';
        return '';
      case 'residence':
        if (!value.trim()) return 'Place of residence is required';
        if (value.length < 2) return 'Must be at least 2 characters';
        if (value.length > 100) return 'Must be less than 100 characters';
        return '';
      default:
        return '';
    }
  };

  const handleBlur = (name) => {
    setTouched({ ...touched, [name]: true });
    const value = { firstName, lastName, email, mobile, residence }[name];
    const error = validateField(name, value);
    setErrors({ ...errors, [name]: error });
  };

  const handleChange = (name, value) => {
    // Update value
    switch (name) {
      case 'firstName': setFirstName(value); break;
      case 'lastName': setLastName(value); break;
      case 'email': setEmail(value); break;
      case 'mobile': setMobile(value); break;
      case 'residence': setResidence(value); break;
    }
    
    // Clear error if field is being edited
    if (touched[name]) {
      const error = validateField(name, value);
      setErrors({ ...errors, [name]: error });
    }
    setGlobalError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate all fields
    const newErrors = {
      firstName: validateField('firstName', firstName),
      lastName: validateField('lastName', lastName),
      email: validateField('email', email),
      mobile: validateField('mobile', mobile),
      residence: validateField('residence', residence),
    };
    
    setErrors(newErrors);
    setTouched({ firstName: true, lastName: true, email: true, mobile: true, residence: true });
    
    // Check if any errors
    if (Object.values(newErrors).some(err => err)) {
      setGlobalError('Please fix the errors above before continuing');
      return;
    }
    
    setGlobalError('');
    try {
      await onSubmit({ 
        firstName: firstName.trim(), 
        lastName: lastName.trim(), 
        email: email.trim().toLowerCase(), 
        mobileNumber: mobile.trim(), 
        placeOfResidence: residence.trim() 
      });
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 405) {
        setGlobalError('Server error: The backend may need to be restarted. Please contact support.');
      } else if (status === 409) {
        const msg = typeof detail === 'object' ? detail?.message : detail;
        setGlobalError(msg || 'A candidate with this email or phone already exists.');
      } else if (status === 401) {
        setGlobalError('Session expired. Please log in again.');
      } else {
        setGlobalError(typeof detail === 'string' ? detail : typeof detail === 'object' ? detail?.message : 'Submission failed. Please try again.');
      }
    }
  };

  const inputClasses = (hasError) => `w-full pl-10 pr-4 py-3 bg-white border ${hasError ? 'border-red-300 focus:border-red-500 focus:ring-red-500/20' : 'border-slate-200 focus:border-primary focus:ring-primary/20'} rounded-xl text-sm text-foreground focus:outline-none focus:ring-2 transition-all`;
  const labelClasses = "block text-sm font-semibold text-slate-700 mb-1.5";
  const iconClasses = (hasError) => `absolute left-3.5 top-3.5 w-4 h-4 ${hasError ? 'text-red-400' : 'text-slate-400'} group-focus-within:text-primary transition-colors`;

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        {/* First Name */}
        <div className="space-y-1">
          <label className={labelClasses}>
            First Name <span className="text-red-500">*</span>
          </label>
          <div className="relative group">
            <User className={iconClasses(touched.firstName && errors.firstName)} />
            <input
              type="text"
              value={firstName}
              onChange={(e) => handleChange('firstName', e.target.value)}
              onBlur={() => handleBlur('firstName')}
              placeholder="John"
              disabled={disabled}
              maxLength={50}
              className={inputClasses(touched.firstName && errors.firstName)}
            />
          </div>
          <AnimatePresence>
            {touched.firstName && errors.firstName && (
              <motion.p 
                initial={{ opacity: 0, height: 0 }} 
                animate={{ opacity: 1, height: 'auto' }} 
                exit={{ opacity: 0, height: 0 }}
                className="text-xs text-red-600 flex items-center gap-1 mt-1"
              >
                <AlertCircle className="w-3 h-3" />
                {errors.firstName}
              </motion.p>
            )}
          </AnimatePresence>
        </div>

        {/* Last Name */}
        <div className="space-y-1">
          <label className={labelClasses}>
            Last Name <span className="text-red-500">*</span>
          </label>
          <div className="relative group">
            <User className={iconClasses(touched.lastName && errors.lastName)} />
            <input
              type="text"
              value={lastName}
              onChange={(e) => handleChange('lastName', e.target.value)}
              onBlur={() => handleBlur('lastName')}
              placeholder="Doe"
              disabled={disabled}
              maxLength={50}
              className={inputClasses(touched.lastName && errors.lastName)}
            />
          </div>
          <AnimatePresence>
            {touched.lastName && errors.lastName && (
              <motion.p 
                initial={{ opacity: 0, height: 0 }} 
                animate={{ opacity: 1, height: 'auto' }} 
                exit={{ opacity: 0, height: 0 }}
                className="text-xs text-red-600 flex items-center gap-1 mt-1"
              >
                <AlertCircle className="w-3 h-3" />
                {errors.lastName}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Email */}
      <div className="space-y-1">
        <label className={labelClasses}>
          Email Address <span className="text-red-500">*</span>
        </label>
        <div className="relative group">
          <Mail className={iconClasses(touched.email && errors.email)} />
          <input
            type="email"
            value={email}
            onChange={(e) => handleChange('email', e.target.value)}
            onBlur={() => handleBlur('email')}
            placeholder="john.doe@example.com"
            disabled={disabled}
            className={inputClasses(touched.email && errors.email)}
          />
        </div>
        {initialEmail && (
          <p className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" />
            Pre-filled from your account
          </p>
        )}
        <AnimatePresence>
          {touched.email && errors.email && (
            <motion.p 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: 'auto' }} 
              exit={{ opacity: 0, height: 0 }}
              className="text-xs text-red-600 flex items-center gap-1 mt-1"
            >
              <AlertCircle className="w-3 h-3" />
              {errors.email}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* Mobile Number */}
      <div className="space-y-1">
        <label className={labelClasses}>
          Mobile Number <span className="text-red-500">*</span>
        </label>
        <div className="relative group">
          <Phone className={iconClasses(touched.mobile && errors.mobile)} />
          <input
            type="tel"
            value={mobile}
            onChange={(e) => handleChange('mobile', e.target.value)}
            onBlur={() => handleBlur('mobile')}
            placeholder="+1 (555) 000-0000"
            disabled={disabled}
            className={inputClasses(touched.mobile && errors.mobile)}
          />
        </div>
        <p className="text-xs text-slate-500 mt-1">Include country code (e.g., +1 for US)</p>
        <AnimatePresence>
          {touched.mobile && errors.mobile && (
            <motion.p 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: 'auto' }} 
              exit={{ opacity: 0, height: 0 }}
              className="text-xs text-red-600 flex items-center gap-1 mt-1"
            >
              <AlertCircle className="w-3 h-3" />
              {errors.mobile}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* Place of Residence */}
      <div className="space-y-1">
        <label className={labelClasses}>
          Place of Residence <span className="text-red-500">*</span>
        </label>
        <div className="relative group">
          <MapPin className={iconClasses(touched.residence && errors.residence)} />
          <input
            type="text"
            value={residence}
            onChange={(e) => handleChange('residence', e.target.value)}
            onBlur={() => handleBlur('residence')}
            placeholder="New York, NY"
            disabled={disabled}
            maxLength={100}
            className={inputClasses(touched.residence && errors.residence)}
          />
        </div>
        <AnimatePresence>
          {touched.residence && errors.residence && (
            <motion.p 
              initial={{ opacity: 0, height: 0 }} 
              animate={{ opacity: 1, height: 'auto' }} 
              exit={{ opacity: 0, height: 0 }}
              className="text-xs text-red-600 flex items-center gap-1 mt-1"
            >
              <AlertCircle className="w-3 h-3" />
              {errors.residence}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      {/* Global Error */}
      <AnimatePresence>
        {globalError && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            exit={{ opacity: 0, height: 0 }}
            className="flex items-start gap-3 text-sm text-red-700 bg-red-50 p-4 rounded-xl border border-red-200"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span className="flex-1">{globalError}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Submit Button */}
      <motion.button
        whileHover={{ scale: disabled ? 1 : 1.02 }}
        whileTap={{ scale: disabled ? 1 : 0.98 }}
        type="submit"
        disabled={disabled}
        className={`w-full flex items-center justify-center gap-2 py-4 px-6 rounded-xl text-base font-semibold text-white transition-all shadow-lg
          ${disabled ? 'bg-primary/50 cursor-not-allowed' : 'bg-gradient-to-r from-primary to-blue-600 hover:from-primary/90 hover:to-blue-600/90 shadow-primary/30 hover:shadow-xl hover:shadow-primary/40'}`}
      >
        {disabled ? (
          <>
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Saving...</span>
          </>
        ) : (
          <>
            <span>Continue to Resume Upload</span>
            <ArrowRight className="w-5 h-5" />
          </>
        )}
      </motion.button>
    </form>
  );
};

export default BasicDetailsForm;
