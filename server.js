const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();

// Middlewares
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Configuração CORS para produção e desenvolvimento
app.use(cors({
  origin: [
    'https://*.vercel.app',
    'http://localhost:3000',
    'http://localhost:8000'
  ],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Servir arquivos estáticos - IMPORTANTE: deve vir ANTES das rotas específicas
app.use(express.static(path.join(__dirname, 'static')));

// Health check para Vercel
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', message: 'Server is running' });
});

app.get('/cities', async (req, res) => {
  try {
    console.log('📞 Rota /cities foi chamada - conectando com backend real');
    
    // ✅ SUBSTITUA pela URL real do seu backend no Render
    const backendUrl = 'https://projeto-site-routelab.onrender.com/cities';
    
    const response = await fetch(backendUrl);
    const data = await response.json();
    
    res.json(data);
  } catch (error) {
    console.error('Erro ao buscar cidades do backend real:', error);
    res.status(500).json({ error: 'Erro ao conectar com o backend' });
  }
});

// ✅ ROTA API CIDADES (se ainda for usada)
app.get('/api/cidades', async (req, res) => {
  try {
    console.log('📞 Rota /api/cidades - conectando com backend real');
    
    // ✅ SUBSTITUA pela URL real do seu backend no Render
    const backendUrl = 'https://projeto-site-routelab.onrender.com/cities';
    
    const response = await fetch(backendUrl);
    const data = await response.json();
    
    res.json(data);
  } catch (error) {
    console.error('Erro ao buscar cidades via /api/cidades:', error);
    res.status(500).json({ error: 'Erro ao conectar com o backend' });
  }
});


// ✅ ROTA COMPETITIVIDADE - COM TRATAMENTO COMPLETO
app.get('/api/competitividade/:cidade', async (req, res) => {
  try {
    const { cidade } = req.params;
    console.log(`📞 Buscando dados reais para: ${cidade}`);
    
    const backendUrl = `https://projeto-site-routelab.onrender.com/api/destinos/${encodeURIComponent(cidade)}`;
    
    const response = await fetch(backendUrl);
    
    if (!response.ok) {
      throw new Error(`Backend respondeu com status: ${response.status}`);
    }
    
    const backendData = await response.json();
    console.log('✅ Dados recebidos do backend:', backendData);
    
    // ✅ Garantir que todos os campos existam
    const frontendData = {
      abrangencia: backendData.abrangencia || 0,
      economia_media: backendData.economia_media || 0,
      co2_media: backendData.co2_media || 0,
      tempo_medio: backendData.tempo_medio || 0,
      total_destinos: backendData.total_destinos || 0,
      destinos_competitivos: backendData.destinos_competitivos || 0,
      top_economia: backendData.top_economia || [],
      alerta_br319_count: backendData.alerta_br319_count || 0,
      alerta_br319_exemplos: backendData.alerta_br319_exemplos || []
      // corredores é ignorado pois o frontend não usa
    };
    
    console.log('📊 Dados enviados para frontend:', {
      cidade: cidade,
      destinos: frontendData.destinos_competitivos,
      economia: frontendData.economia_media
    });
    
    res.json(frontendData);
    
  } catch (error) {
    console.error('❌ Erro ao buscar dados de competitividade:', error);
    res.status(500).json({ 
      error: 'Erro ao conectar com o backend',
      details: error.message 
    });
  }
});

// ✅ ROTAS ESPECÍFICAS PARA HTML - DEVEM VIR DEPOIS DO static
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

app.get('/competitividade', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'competitividade.html'));
});

// ✅ Rota fallback para SPA - IMPORTANTE PARA VERCEL
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Tratamento de erros global
app.use((error, req, res, next) => {
  console.error('Erro não tratado:', error);
  res.status(500).json({ error: 'Erro interno do servidor' });
});

// Configuração da porta para Vercel
const PORT = process.env.PORT || 3000;

// Inicialização do servidor
app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});

module.exports = app;