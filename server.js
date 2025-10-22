const express = require("express");
const cors = require("cors");
const xlsx = require('xlsx');
const path = require("path");
const fs = require("fs"); // Adicione esta linha

const app = express();
app.use(cors());

// ===== Verificação do caminho do arquivo =====
const filePath = path.join(__dirname, "data", "Network-cidades.xlsx");

// Verifica se o arquivo existe
if (!fs.existsSync(filePath)) {
    console.error("❌ Arquivo não encontrado:", filePath);
    console.log("Diretório atual:", __dirname);
    
    // Lista arquivos no diretório data (se existir)
    const dataDir = path.join(__dirname, "data");
    if (fs.existsSync(dataDir)) {
        console.log("Arquivos no diretório data:", fs.readdirSync(dataDir));
    }
    
    process.exit(1);
}

console.log("✅ Arquivo encontrado:", filePath);

// ===== Leitura do Excel =====
try {
    const workbook = xlsx.readFile(filePath, { cellDates: true });
    
    // Mostra abas disponíveis
    console.log("📋 Abas disponíveis:", workbook.SheetNames);
    
    // Verifica se a aba "Data" existe
    if (!workbook.SheetNames.includes('Data')) {
        console.error("❌ Aba 'Data' não encontrada. Abas disponíveis:", workbook.SheetNames);
        process.exit(1);
    }
    
    // Obtém a aba corretamente
    const sheet = workbook.Sheets['Data'];
    
    // Converte para JSON
    const data = xlsx.utils.sheet_to_json(sheet, { 
        defval: null, 
        raw: false,
        header: 1 // Adiciona esta opção para debug
    });
    
    console.log("📊 Número de linhas:", data.length);
    
    if (data.length > 0) {
        console.log("🏷️ Colunas detectadas:", Object.keys(data[0]));
        console.log("📝 Exemplo de dados lidos:", data.slice(0, 3));
    } else {
        console.log("⚠ Nenhum dado encontrado na aba 'Data'");
        
        // Verifica se há dados brutos na planilha
        const range = xlsx.utils.decode_range(sheet['!ref']);
        console.log("Intervalo da planilha:", sheet['!ref']);
        console.log("Número de linhas brutas:", range.e.r + 1);
    }
    
    // ===== Rotas =====
    // ... (seu código de rotas continua aqui)
    
} catch (error) {
    console.error("❌ Erro ao ler o arquivo Excel:", error.message);
    process.exit(1);
}

// ===== Rotas =====

// Lista paginada
app.get("/dados", (req, res) => {
  let { page = 1, limit = 50 } = req.query;
  page = parseInt(page);
  limit = parseInt(limit);

  const start = (page - 1) * limit;
  const end = page * limit;

  res.json({
    total: data.length,
    page,
    limit,
    results: data.slice(start, end),
  });
});

// Filtro por coluna
app.get("/filtro", (req, res) => {
  const { coluna, valor } = req.query;
  if (!coluna || !valor) {
    return res
      .status(400)
      .json({ error: "Faltam parâmetros coluna e valor" });
  }
  const filtrados = data.filter((row) => String(row[coluna]) === valor);
  res.json(filtrados);
});

// Start
app.listen(3000, () => {
  console.log("API rodando em http://localhost:3000");
});
