import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { FileSearch, Clock, CheckCircle2 } from 'lucide-react';

/**
 * Componente de Processamento
 * Exibe animação de carregamento enquanto o documento é processado
 */
export default function ProcessingSection({ fileName, progress = 0 }) {
  const [dots, setDots] = useState('');
  const [currentStep, setCurrentStep] = useState(0);

  // Animação dos pontos
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => prev.length >= 3 ? '' : prev + '.');
    }, 500);
    return () => clearInterval(interval);
  }, []);

  // Simula progresso das etapas
  useEffect(() => {
    if (progress < 30) setCurrentStep(0);
    else if (progress < 60) setCurrentStep(1);
    else if (progress < 90) setCurrentStep(2);
    else setCurrentStep(3);
  }, [progress]);

  const steps = [
    { label: 'Enviando documento', icon: FileSearch },
    { label: 'Analisando conteúdo', icon: FileSearch },
    { label: 'Extraindo dados', icon: FileSearch },
    { label: 'Finalizando', icon: CheckCircle2 },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-xl mx-auto text-center"
    >
      {/* Animação Principal */}
      <div className="relative mb-12">
        {/* Círculos de fundo animados */}
        <motion.div
          animate={{ scale: [1, 1.2, 1], opacity: [0.1, 0.2, 0.1] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <div className="w-48 h-48 bg-blue-500 rounded-full" />
        </motion.div>
        
        <motion.div
          animate={{ scale: [1.1, 1, 1.1], opacity: [0.15, 0.25, 0.15] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
          className="absolute inset-0 flex items-center justify-center"
        >
          <div className="w-36 h-36 bg-blue-500 rounded-full" />
        </motion.div>

        {/* Ícone central */}
        <div className="relative z-10 flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
            className="w-32 h-32 rounded-full border-4 border-blue-100 border-t-blue-600 flex items-center justify-center bg-white shadow-2xl"
          >
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <FileSearch className="w-12 h-12 text-blue-600" />
            </motion.div>
          </motion.div>
        </div>
      </div>

      {/* Texto Principal */}
      <h2 className="text-2xl font-semibold text-gray-900 mb-3">
        Processando documento{dots}
      </h2>
      
      <p className="text-gray-500 mb-2">
        Isso pode levar alguns minutos
      </p>

      {fileName && (
        <p className="text-sm text-gray-400 mb-8 truncate max-w-sm mx-auto">
          {fileName}
        </p>
      )}

      {/* Barra de Progresso */}
      <div className="relative mb-8">
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
          />
        </div>
        <p className="text-sm text-gray-500 mt-2">{Math.round(progress)}%</p>
      </div>

      {/* Etapas do Processamento */}
      <div className="flex justify-center gap-2 flex-wrap">
        {steps.map((step, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0.3 }}
            animate={{ 
              opacity: index <= currentStep ? 1 : 0.3,
              scale: index === currentStep ? 1.1 : 1
            }}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium
              ${index < currentStep 
                ? 'bg-green-100 text-green-700' 
                : index === currentStep 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-gray-100 text-gray-400'
              }
            `}
          >
            {index < currentStep ? (
              <CheckCircle2 className="w-3.5 h-3.5" />
            ) : index === currentStep ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Clock className="w-3.5 h-3.5" />
              </motion.div>
            ) : null}
            <span className="hidden sm:inline">{step.label}</span>
          </motion.div>
        ))}
      </div>

      {/* Aviso */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2 }}
        className="text-xs text-gray-400 mt-12"
      >
        Por favor, não feche esta página durante o processamento
      </motion.p>
    </motion.div>
  );
}
