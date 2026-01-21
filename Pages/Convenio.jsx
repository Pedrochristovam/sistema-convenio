import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import UploadSection from '../components/convenio/UploadSection.jsx';
import ProcessingSection from '../components/convenio/ProcessingSection.jsx';
import ResultSection from '../components/convenio/ResultSection.jsx';
import ConvenioResultSection from '../components/convenio/ConvenioResultSection.jsx';

// Configuração da API
// Importante: para evitar desencontro de portas durante os testes locais,
// fixamos o backend em 8000 (o backend também está fixo em 8000).
const API_BASE_URL = 'http://localhost:8000';

/**
 * Página principal de Processamento de Convênio
 * Gerencia os estados: upload, processamento e resultado
 */
export default function Convenio() {
  // Estados da aplicação
  const [currentStep, setCurrentStep] = useState('upload'); // 'upload' | 'processing' | 'result'
  const [selectedFile, setSelectedFile] = useState(null); // File | File[] | null
  const [processId, setProcessId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  const selectedFiles = Array.isArray(selectedFile) ? selectedFile : (selectedFile ? [selectedFile] : []);

  /**
   * Inicia o upload e processamento do arquivo
   */
  const handleProcess = async () => {
    if (!selectedFile) return;

    setCurrentStep('processing');
    setProgress(0);
    setError(null);

    try {
      // Prepara FormData para upload
      const formData = new FormData();
      const files = Array.isArray(selectedFile) ? selectedFile : [selectedFile];

      // Monta payload conforme endpoint
      if (files.length > 1) {
        files.forEach((fileItem) => {
          formData.append('files', fileItem, fileItem.name);
        });
      } else {
        formData.append('file', files[0], files[0].name);
      }

      // POST /upload (1 arquivo) | /upload_batch (múltiplos)
      const uploadEndpoint = files.length > 1 ? `${API_BASE_URL}/upload_batch` : `${API_BASE_URL}/upload`;
      const uploadResponse = await fetch(uploadEndpoint, {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Erro ao enviar arquivo');
      }

      const uploadData = await uploadResponse.json();
      const jobId = uploadData.job_id;
      setProcessId(jobId);

      // Polling do resultado (espera processamento)
      let attempts = 0;
      const maxAttempts = 300; // 5 minutos (para PDFs grandes)
      
      const checkStatus = async () => {
        try {
          // PASSO 1: Verifica STATUS do job
          const statusResponse = await fetch(`${API_BASE_URL}/status/${jobId}`);
          
          if (!statusResponse.ok) {
            throw new Error(`Erro ao verificar status: ${statusResponse.status}`);
          }
          
          const statusData = await statusResponse.json();
          console.log('📊 Status do job:', statusData);
          
          if (statusData.status === 'done') {
            // PASSO 2: Busca RESULTADO completo
            console.log('✅ Processamento concluído! Buscando resultado...');
            setProgress(95);
            
            const resultResponse = await fetch(`${API_BASE_URL}/result/${jobId}`);
            if (!resultResponse.ok) {
              throw new Error(`Erro ao buscar resultado: ${resultResponse.status}`);
            }
            
            const resultData = await resultResponse.json();
            console.log('📦 Resultado recebido:', resultData);
            
            setProgress(100);
            setResultData(resultData.items || []);
            setCurrentStep('result');
            
          } else if (statusData.status === 'error') {
            throw new Error(statusData.message || 'Erro no processamento');
            
          } else if (statusData.status === 'processing' || statusData.status === 'pending') {
            // Ainda processando
            attempts++;
            if (attempts < maxAttempts) {
              // Usa o progresso REAL da API (0-100) ou simula
              const apiProgress = statusData.progress || 0;
              const simulatedProgress = 10 + Math.min(85, (attempts / maxAttempts) * 85);
              const finalProgress = Math.max(apiProgress, simulatedProgress);
              
              console.log(`⏳ Processando... ${finalProgress.toFixed(0)}% (tentativa ${attempts}/${maxAttempts})`);
              setProgress(finalProgress);
              
              setTimeout(checkStatus, 3000); // Verifica a cada 3 segundos (PDF grande)
            } else {
              throw new Error('Timeout: processamento demorou muito (5 min). Documento muito grande?');
            }
          }
        } catch (err) {
          console.error('❌ Erro ao verificar status:', err);
          setError(err.message || 'Erro ao processar arquivo');
          setCurrentStep('upload');
        }
      };
      
      // Inicia polling
      setTimeout(checkStatus, 2000);

    } catch (err) {
      console.error('Erro no upload:', err);
      setError(err.message || 'Erro ao processar arquivo');
      setCurrentStep('upload');
    }
  };

  /**
   * Exporta dados para Excel
   */
  const handleExport = async () => {
    if (!resultData || resultData.length === 0) return;

    setIsExporting(true);

    try {
      // Cria conteúdo CSV (compatível com Excel)
      const headers = ['Banco', 'Agência', 'Conta', 'Tipo de Conta', 'CPF/CNPJ', 'Valor'];
      const rows = resultData.map(item => [
        item.banco || '',
        item.agencia || '',
        item.conta || '',
        item.tipo_conta || '',
        item.cpf_cnpj || '',
        item.valor?.toString().replace('.', ',') || ''
      ]);

      // BOM para UTF-8 no Excel
      const BOM = '\uFEFF';
      const csvContent = BOM + [
        headers.join(';'),
        ...rows.map(row => row.join(';'))
      ].join('\r\n');

      // Cria blob e download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `convenio_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

    } catch (err) {
      console.error('Erro na exportação:', err);
      setError('Erro ao exportar arquivo');
    } finally {
      setIsExporting(false);
    }
  };

  /**
   * Reinicia para novo upload
   */
  const handleNewUpload = () => {
    setSelectedFile(null);
    setProcessId(null);
    setProgress(0);
    setResultData(null);
    setError(null);
    setCurrentStep('upload');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50">
      {/* Background decorativo */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
      </div>

      {/* Container principal */}
      <div className="relative z-10 container mx-auto px-4 py-12 md:py-20">
        {/* Logo/Branding */}
        <div className="flex justify-center mb-12">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-200">
              <span className="text-white font-bold text-lg">C</span>
            </div>
            <span className="text-xl font-semibold text-gray-800">ConvênioProc</span>
          </div>
        </div>

        {/* Mensagem de Erro Global */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-xl mx-auto mb-8 p-4 bg-red-50 border border-red-100 rounded-xl text-center"
            >
              <p className="text-red-600">{error}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm text-red-500 hover:text-red-700 underline"
              >
                Fechar
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Conteúdo baseado no step atual */}
        <AnimatePresence mode="wait">
          {currentStep === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <UploadSection
                selectedFile={selectedFile}
                onFileSelect={setSelectedFile}
                onProcess={handleProcess}
                isProcessing={false}
              />
            </motion.div>
          )}

          {currentStep === 'processing' && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <ProcessingSection
                fileName={
                  selectedFiles.length > 1
                    ? `${selectedFiles.length} arquivos selecionados`
                    : (selectedFiles[0]?.name || '')
                }
                progress={progress}
              />
            </motion.div>
          )}

          {currentStep === 'result' && (
            <motion.div
              key="result"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {resultData && resultData.length > 0 && (resultData[0].tipo_documento === 'EXTRATO_CONVENIO_MOVIMENTACAO' || resultData[0].movimentacoes) ? (
                <ConvenioResultSection
                  data={resultData}
                  onExport={handleExport}
                  onNewUpload={handleNewUpload}
                  isExporting={isExporting}
                />
              ) : (
                <ResultSection
                  data={resultData}
                  onExport={handleExport}
                  onNewUpload={handleNewUpload}
                  isExporting={isExporting}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer */}
        <footer className="mt-16 text-center text-sm text-gray-400">
          <p>© {new Date().getFullYear()} ConvênioProc. Todos os direitos reservados.</p>
        </footer>
      </div>
    </div>
  );
}
