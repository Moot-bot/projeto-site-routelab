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

// Suas rotas API aqui...
app.get('/api/cidades', async (req, res) => {
  try {
    // Simulação de dados - substitua com sua lógica real
    const cidades = [
      { id: 1, nome: 'São Paulo' },
      { id: 2, nome: 'Rio de Janeiro' },
      { id: 3, nome: 'Santos' }
    ];
    res.json(cidades);
  } catch (error) {
    console.error('Erro ao buscar cidades:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

// Rota para dados de competitividade
app.get('/cities', async (req, res) => {
  try {
    console.log('📞 Rota /cities foi chamada');
    const cidades = [
      { id: 1, nome: 'São Paulo' },
      { id: 2, nome: 'Rio de Janeiro' },
      { id: 3, nome: 'Santos' }
    ];
    // ✅ Formato correto: { cities: array }
    res.json({ 
      cities: cidades.map(c => c.nome) 
    });
  } catch (error) {
    console.error('Erro em /cities:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
  }
});
app.get('/api/competitividade/:cidade', async (req, res) => {
  try {
    const { cidade } = req.params;
    // Simulação de dados - substitua com sua lógica real
    const dados = {
      cidade: cidade,
      economia: 15.5,
      reducaoCO2: 30.2,
      destinos: [
        { nome: 'Destino A', economia: 25 },
        { nome: 'Destino B', economia: 18 }
      ]
    };
    res.json(dados);
  } catch (error) {
    console.error('Erro ao buscar dados de competitividade:', error);
    res.status(500).json({ error: 'Erro interno do servidor' });
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