import React from 'react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { FileText, Cpu, ShieldAlert, Search, Network, Video, ChevronRight, CheckCircle2 } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: 'AI Resume Parser',
      description: 'Instantly extract skills, experience, and education from any resume format with high accuracy.',
      icon: <FileText className="w-6 h-6 text-primary" />,
      color: 'bg-primary/10'
    },
    {
      title: 'Talent Intelligence',
      description: 'Smart candidate matching using advanced AI to find the perfect fit for your roles.',
      icon: <Cpu className="w-6 h-6 text-secondary" />,
      color: 'bg-secondary/10'
    },
    {
      title: 'Fraud Detection',
      description: 'Automated integrity checks and risk assessment to ensure candidate authenticity.',
      icon: <ShieldAlert className="w-6 h-6 text-destructive" />,
      color: 'bg-destructive/10'
    },
    {
      title: 'Semantic Candidate Search',
      description: 'Search your candidate database using natural language and semantic meaning.',
      icon: <Search className="w-6 h-6 text-success" />,
      color: 'bg-success/10'
    },
    {
      title: 'Skill Graph Visualization',
      description: 'Visualize candidate capabilities and find hidden overlaps between different skill sets.',
      icon: <Network className="w-6 h-6 text-warning" />,
      color: 'bg-warning/10'
    },
    {
      title: 'Video Interview Analysis',
      description: 'AI-evaluated video screening evaluating communication, confidence, and context.',
      icon: <Video className="w-6 h-6 text-primary" />,
      color: 'bg-primary/10'
    }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans overflow-hidden">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 w-full backdrop-blur-md bg-white/70 border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2 cursor-pointer" onClick={() => navigate('/')}>
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <Cpu className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight text-foreground">
                Hire<span className="text-primary">AI</span>
              </span>
            </div>
            
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Features</a>
              <a href="#solutions" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Solutions</a>
              <a href="#resources" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Resources</a>
              <a href="#pricing" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Pricing</a>
            </div>

            <div className="flex items-center space-x-4">
              <Link to="/login" className="text-sm font-medium text-foreground hover:text-primary transition-colors hidden sm:block">
                Sign In
              </Link>
              <Link to="/login" className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium transition-colors border border-transparent rounded-lg shadow-sm text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary">
                Get Demo
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-20 pb-32 lg:pt-32 lg:pb-40 overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute inset-0 z-0 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob"></div>
          <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-1/3 w-96 h-96 bg-success/20 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-blob animation-delay-4000"></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-foreground mb-6 leading-tight">
              Expose Your Resume.<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
                Expand Your Opportunities.
              </span>
            </h1>
            <p className="mt-4 max-w-2xl text-xl text-muted-foreground mx-auto">
              AI-powered recruitment platform that connects top talent with the right opportunities.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/login">
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-8 py-3.5 text-base font-medium rounded-xl shadow-soft text-white bg-primary hover:bg-primary/90 flex items-center"
                >
                  Get Started <ChevronRight className="ml-2 w-5 h-5" />
                </motion.button>
              </Link>
              <p className="text-sm text-muted-foreground flex items-center">
                <CheckCircle2 className="w-4 h-4 mr-1 text-success" /> No credit card required
              </p>
            </div>
          </motion.div>
        </div>

        {/* Floating UI Elements */}
        <div className="hidden lg:block absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-7xl h-full pointer-events-none z-0">
          <motion.div 
            animate={{ y: [0, -15, 0] }} 
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="absolute top-20 left-10 p-4 bg-white rounded-xl shadow-glass border border-white/40 backdrop-blur-sm"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-900">Resume Parsed</div>
                <div className="text-xs text-green-600 font-medium">100% Match</div>
              </div>
            </div>
          </motion.div>

          <motion.div 
            animate={{ y: [0, 20, 0] }} 
            transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
            className="absolute bottom-20 right-10 p-4 bg-white rounded-xl shadow-glass border border-white/40 backdrop-blur-sm"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <Network className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-sm font-semibold text-gray-900">Skill Graph Built</div>
                <div className="text-xs text-gray-500">React, Node.js, AI</div>
              </div>
            </div>
          </motion.div>

          <motion.div 
            animate={{ y: [0, -10, 0] }} 
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut", delay: 2 }}
            className="absolute top-40 right-20 p-3 bg-white rounded-xl shadow-glass border border-white/40 backdrop-blur-sm flex items-center"
          >
             <div className="flex -space-x-2">
                <div className="w-8 h-8 rounded-full bg-gray-200 border-2 border-white" />
                <div className="w-8 h-8 rounded-full bg-blue-200 border-2 border-white" />
                <div className="w-8 h-8 rounded-full bg-green-200 border-2 border-white flex items-center justify-center text-xs font-medium text-green-800">+5</div>
              </div>
              <div className="ml-3 text-xs font-semibold text-gray-700">New Matches</div>
          </motion.div>
        </div>
      </section>

      {/* About Section */}
      <section id="features" className="py-24 bg-card relative z-10 border-t border-border/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-base text-primary font-semibold tracking-wide uppercase">About Platform</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-foreground sm:text-4xl">
              Next-Generation Talent Acquisition
            </p>
            <p className="mt-4 max-w-2xl text-xl text-muted-foreground mx-auto">
              A comprehensive suite of AI tools designed to streamline recruitment, eliminate bias, and find the perfect fit faster.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                whileHover={{ y: -5, scale: 1.02 }}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="relative p-6 bg-white rounded-2xl shadow-sm border border-border/50 hover:shadow-soft hover:border-primary/20 transition-all duration-300 group"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${feature.color} mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      
      {/* Testimonial / Social Proof Section */}
      <section className="py-20 bg-muted/50 text-center">
         <div className="max-w-4xl mx-auto px-4">
            <h2 className="text-2xl font-bold text-foreground mb-10">Trusted by fast-growing companies</h2>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-50 grayscale transition-all hover:grayscale-0 hover:opacity-100">
               {/* Placeholders for logos */}
               <div className="flex items-center text-xl font-bold tracking-tighter"><span className="text-primary mr-1">◆</span> ACME Corp</div>
               <div className="flex items-center text-xl font-bold tracking-tighter"><span className="text-secondary mr-1">▲</span> GlobalTech</div>
               <div className="flex items-center text-xl font-bold tracking-tighter"><span className="text-success mr-1">●</span> Innovate</div>
               <div className="flex items-center text-xl font-bold tracking-tighter"><span className="text-warning mr-1">■</span> NexaBuild</div>
            </div>
         </div>
      </section>

      {/* Footer */}
      <footer className="bg-white py-12 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center space-x-2 mb-4 md:mb-0 text-foreground font-bold">
            <Cpu className="w-5 h-5 text-primary" />
            <span>HireAI</span>
          </div>
          <p className="text-sm text-muted-foreground">
            &copy; 2026 HireAI Platform. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
