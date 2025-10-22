// debug-excel.js
const xlsx = require('xlsx');
const path = require('path');
const fs = require('fs');

console.log("🔍 INICIANDO DEBUG DO EXCEL...\n");

// Caminho do arquivo
const filePath = path.join(__dirname, "data", "Network Results V2.xlsx");
console.log("📁 Caminho do arquivo:", filePath);

// Verifica se o arquivo existe
if (!fs.existsSync(filePath)) {
    console.log("❌ Arquivo não encontrado!");
    console.log("📂 Diretório atual:", __dirname);
    
    const dataDir = path.join(__dirname, "data");
    if (fs.existsSync(dataDir)) {
        console.log("📋 Arquivos na pasta 'data':", fs.readdirSync(dataDir));
    }
    process.exit(1);
}

console.log("✅ Arquivo encontrado!\n");

try {
    // Lê o arquivo Excel
    const workbook = xlsx.readFile(filePath);
    
    console.log("📊 ABAS DISPONÍVEIS:");
    console.log(workbook.SheetNames);
    console.log("");
    
    // Analisa cada aba
    workbook.SheetNames.forEach(sheetName => {
        console.log(`🔍 ANALISANDO ABA: "${sheetName}"`);
        const sheet = workbook.Sheets[sheetName];
        
        // Informações básicas da aba
        console.log("   📐 Range definido:", sheet['!ref'] || "NÃO DEFINIDO");
        console.log("   🔢 Número de células:", Object.keys(sheet).length - 1);
        
        // Lista algumas células para ver a estrutura
        const cellKeys = Object.keys(sheet)
            .filter(key => key !== '!ref' && key !== '!margins')
            .slice(0, 10); // Apenas as primeiras 10 células
        
        console.log("   🎯 Primeiras células:", cellKeys);
        
        // Mostra o conteúdo de algumas células
        cellKeys.forEach(key => {
            console.log(`      ${key}: ${JSON.stringify(sheet[key])}`);
        });
        
        console.log("");
    });
    
    // Foca na aba "Data" para análise detalhada
    console.log("🎯 ANÁLISE DETALHADA DA ABA 'Data':");
    const dataSheet = workbook.Sheets['Data'];
    
    if (!dataSheet) {
        console.log("❌ Aba 'Data' não encontrada!");
        return;
    }
    
    console.log("Range:", dataSheet['!ref'] || "Não definido");
    
    // Tenta diferentes métodos de leitura
    console.log("\n🧪 TESTANDO DIFERENTES MÉTODOS DE LEITURA:");
    
    // Método 1: Normal
    try {
        const data1 = xlsx.utils.sheet_to_json(dataSheet, { defval: null, raw: false });
        console.log("1️⃣  Método normal - Linhas:", data1.length);
        if (data1.length > 0) {
            console.log("   Primeira linha:", JSON.stringify(data1[0], null, 2));
        }
    } catch (e) {
        console.log("1️⃣  ❌ Erro no método normal:", e.message);
    }
    
    // Método 2: Como array
    try {
        const data2 = xlsx.utils.sheet_to_json(dataSheet, { header: 1 });
        console.log("2️⃣  Como array - Linhas:", data2.length);
        if (data2.length > 0) {
            console.log("   Primeira linha:", data2[0]);
        }
    } catch (e) {
        console.log("2️⃣  ❌ Erro no método array:", e.message);
    }
    
    // Método 3: Com range manual
    try {
        // Se não tem range, tenta definir um manualmente
        if (!dataSheet['!ref']) {
            console.log("   ⚠️  Tentando com range manual A1:Z100...");
            const manualRange = {s: {c: 0, r: 0}, e: {c: 25, r: 99}};
            dataSheet['!ref'] = xlsx.utils.encode_range(manualRange);
        }
        
        const data3 = xlsx.utils.sheet_to_json(dataSheet, { defval: null });
        console.log("3️⃣  Com range manual - Linhas:", data3.length);
    } catch (e) {
        console.log("3️⃣  ❌ Erro com range manual:", e.message);
    }
    
    console.log("\n💡 DICAS:");
    console.log("• Verifique se a aba 'Data' realmente contém dados");
    console.log("• No Excel, converta tabelas para 'Intervalo'");
    console.log("• Confirme que os dados começam na célula A1");
    console.log("• Verifique se não há linhas/colunas ocultas");
    
} catch (error) {
    console.log("❌ ERRO GERAL:", error.message);
}