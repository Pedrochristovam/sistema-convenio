import React, { useRef, useState } from 'react';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Componente de Upload de PDF
 * Permite arrastar e soltar ou selecionar arquivo PDF
 */
export default function UploadSection({ onFileSelect, onProcess, selectedFile, isProcessing }) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');

  // Valida se o arquivo é PDF
  const validateFile = (file) => {
    if (!file) return false;
    
    if (file.type !== 'application/pdf') {
      setError('Por favor, selecione apenas arquivos PDF.');
      return false;
    }
    
    // Limite de 100MB
    if (file.size > 100 * 1024 * 1024) {
      setError('O arquivo deve ter no máximo 100MB.');
      return false;
    }
    
    setError('');
    return true;
  };

  // Handler para seleção de arquivo
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      onFileSelect(file);
    }
  };

  // Handlers para drag and drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files?.[0];
    if (file && validateFile(file)) {
      onFileSelect(file);
    }
  };

  // Remove arquivo selecionado
  const handleRemoveFile = () => {
    onFileSelect(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Formata tamanho do arquivo
  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-2xl mx-auto"
    >
      {/* Cabeçalho */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-semibold text-gray-900 mb-2">
          Processamento de Convênio
        </h1>
        <p className="text-gray-500">
          Faça upload do documento PDF para extrair as informações bancárias
        </p>
      </div>

      {/* Área de Upload */}
      <div
        onClick={() => !selectedFile && fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-2xl p-12
          transition-all duration-300 ease-out
          ${isDragging 
            ? 'border-blue-500 bg-blue-50 scale-[1.02]' 
            : selectedFile 
              ? 'border-green-300 bg-green-50/50' 
              : 'border-gray-200 bg-gray-50/50 hover:border-blue-300 hover:bg-blue-50/30'
          }
          ${!selectedFile ? 'cursor-pointer' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          className="hidden"
        />

        <AnimatePresence mode="wait">
          {!selectedFile ? (
            <motion.div
              key="upload-prompt"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center"
            >
              <div className={`
                w-20 h-20 rounded-full flex items-center justify-center mb-6
                transition-colors duration-300
                ${isDragging ? 'bg-blue-100' : 'bg-gray-100'}
              `}>
                <Upload className={`w-10 h-10 ${isDragging ? 'text-blue-600' : 'text-gray-400'}`} />
              </div>
              
              <p className="text-lg font-medium text-gray-700 mb-2">
                {isDragging ? 'Solte o arquivo aqui' : 'Arraste e solte seu PDF aqui'}
              </p>
              <p className="text-sm text-gray-400 mb-4">ou</p>
              <button
                type="button"
                className="px-6 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 shadow-sm"
              >
                Selecionar arquivo
              </button>
              <p className="text-xs text-gray-400 mt-4">
                Apenas arquivos PDF • Máximo 100MB
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="file-selected"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-red-100 rounded-xl flex items-center justify-center">
                  <FileText className="w-7 h-7 text-red-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 truncate max-w-xs">
                    {selectedFile.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>
              
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Remover arquivo"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Mensagem de Erro */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-4 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <p className="text-sm text-red-600">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Botão Processar */}
      <motion.button
        onClick={onProcess}
        disabled={!selectedFile || isProcessing}
        whileHover={{ scale: selectedFile && !isProcessing ? 1.02 : 1 }}
        whileTap={{ scale: selectedFile && !isProcessing ? 0.98 : 1 }}
        className={`
          w-full mt-8 py-4 px-8 rounded-xl font-semibold text-lg
          transition-all duration-300 shadow-lg
          ${selectedFile && !isProcessing
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:shadow-blue-200 hover:shadow-xl'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed shadow-none'
          }
        `}
      >
        Processar Convênio
      </motion.button>
    </motion.div>
  );
}
