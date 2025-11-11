/**
 * PraiasSP Tools - Riviera Ingestor
 * Frontend JavaScript
 */

// ================================
// CONFIGURAÇÃO E UTILITÁRIOS
// ================================

// Chamadas de API devem apontar para o backend no Render (não rodamos funções Python no Vercel)
const API_BASE = "https://praiassp-tools.onrender.com/api";

// Formatação de valores monetários
function formatarMoeda(valor) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(valor || 0);
}

// Formatação de data
function formatarData(data) {
  return new Intl.DateTimeFormat("pt-BR").format(new Date(data));
}

// Mostrar mensagem
function mostrarMensagem(elemento, tipo, mensagem) {
  const alertClass = `alert-${tipo}`;
  const html = `
        <div class="alert ${alertClass}">
            <span class="alert-icon">${tipo === "success" ? "✓" : "⚠️"}</span>
            <div class="alert-message">${mensagem}</div>
        </div>
    `;
  document.querySelector(elemento).innerHTML = html;
  setTimeout(() => {
    document.querySelector(elemento).innerHTML = "";
  }, 5000);
}

// Loading spinner
function mostrarLoading(elemento) {
  document.querySelector(elemento).innerHTML =
    '<div class="loading"></div> Processando...';
}

function esconderLoading(elemento) {
  document.querySelector(elemento).innerHTML = "";
}

// ================================
// FUNÇÕES DE API
// ================================

async function fetchDados(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: options.method || "GET",
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      body: options.body ? JSON.stringify(options.body) : null,
    });

    if (!response.ok) {
      throw new Error(`Erro ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Erro na requisição:", error);
    throw error;
  }
}

// ================================
// DASHBOARD
// ================================

async function carregarDashboard() {
  try {
    const data = await fetchDados("/resumo");

    if (data.status === "success") {
      const { obras, totais } = data.resumo;

      // Atualizar cards de métricas
      document.getElementById("despesas-totais").textContent = formatarMoeda(
        totais.despesas_totais
      );
      document.getElementById("aportes-rateados").textContent = formatarMoeda(
        totais.aportes_rateados
      );
      document.getElementById("rentabilidade").textContent = formatarMoeda(
        totais.rentabilidade
      );

      // Calcular saldo final
      const saldoFinal =
        totais.aportes_rateados + totais.rentabilidade - totais.despesas_totais;
      document.getElementById("saldo-final").textContent =
        formatarMoeda(saldoFinal);

      // Atualizar tabela de obras
      const tbody = document.getElementById("tbody-obras");
      tbody.innerHTML = "";

      obras.forEach((obra) => {
        const saldo =
          obra.aportes_rateados + obra.rentabilidade - obra.despesas_totais;
        const row = `
                    <tr>
                        <td>${obra.codigo_obra}</td>
                        <td>${obra.obra_nome || "-"}</td>
                        <td class="text-right">${formatarMoeda(
                          obra.despesas_totais
                        )}</td>
                        <td class="text-right">${formatarMoeda(
                          obra.aportes_rateados
                        )}</td>
                        <td class="text-right">${formatarMoeda(
                          obra.rentabilidade
                        )}</td>
                        <td class="text-right ${
                          saldo < 0 ? "text-danger" : "text-success"
                        }">${formatarMoeda(saldo)}</td>
                    </tr>
                `;
        tbody.innerHTML += row;
      });
    }
  } catch (error) {
    console.error("Erro ao carregar dashboard:", error);
    mostrarMensagem("#mensagem-upload", "danger", "Erro ao carregar dashboard");
  }
}

// ================================
// UPLOAD DE PDFs
// ================================

let arquivosSelecionados = [];

document.getElementById("fileInput")?.addEventListener("change", function (e) {
  arquivosSelecionados = Array.from(e.target.files);
  atualizarListaArquivos();
});

function atualizarListaArquivos() {
  const lista = document.getElementById("arquivo-lista");

  if (arquivosSelecionados.length === 0) {
    lista.innerHTML = "";
    return;
  }

  const html = `
        <div class="alert alert-info">
            <span class="alert-icon">ℹ️</span>
            <div class="alert-message">
                <strong>${
                  arquivosSelecionados.length
                }</strong> arquivo(s) selecionado(s)
                <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                    ${arquivosSelecionados
                      .map(
                        (f) =>
                          `<li>${f.name} (${(f.size / 1024 / 1024).toFixed(
                            2
                          )} MB)</li>`
                      )
                      .join("")}
                </ul>
            </div>
        </div>
    `;
  lista.innerHTML = html;
}

document
  .getElementById("btn-upload")
  ?.addEventListener("click", async function () {
    if (arquivosSelecionados.length === 0) {
      mostrarMensagem(
        "#mensagem-upload",
        "warning",
        "Selecione pelo menos um arquivo"
      );
      return;
    }

    mostrarLoading("#mensagem-upload");

    try {
      const formData = new FormData();
      arquivosSelecionados.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.status === "success") {
        mostrarMensagem(
          "#mensagem-upload",
          "success",
          `${data.total} arquivo(s) carregado(s) com sucesso!`
        );
        arquivosSelecionados = [];
        document.getElementById("fileInput").value = "";
        atualizarListaArquivos();

        // Recarregar dashboard após 2 segundos
        setTimeout(carregarDashboard, 2000);
      } else {
        mostrarMensagem(
          "#mensagem-upload",
          "danger",
          data.erros?.join(", ") || "Erro ao fazer upload"
        );
      }
    } catch (error) {
      console.error("Erro:", error);
      mostrarMensagem(
        "#mensagem-upload",
        "danger",
        "Erro ao fazer upload dos arquivos"
      );
    }

    esconderLoading("#mensagem-upload");
  });

document.getElementById("btn-limpar")?.addEventListener("click", function () {
  arquivosSelecionados = [];
  document.getElementById("fileInput").value = "";
  atualizarListaArquivos();
});

// ================================
// MOVIMENTOS
// ================================

async function carregarMovimentos(competencia = "", codigoObra = "") {
  try {
    let url = "/movimentos";
    const params = new URLSearchParams();

    if (competencia) params.append("competencia", competencia);
    if (codigoObra) params.append("codigo_obra", codigoObra);

    if (params.toString()) url += "?" + params.toString();

    const data = await fetchDados(url);

    if (data.status === "success") {
      const tbody = document.getElementById("tbody-movimentos");
      tbody.innerHTML = "";

      if (data.data.length === 0) {
        tbody.innerHTML =
          '<tr><td colspan="6" class="text-center">Nenhum movimento encontrado</td></tr>';
        return;
      }

      data.data.forEach((mov) => {
        const row = `
                    <tr>
                        <td>${mov.competencia}</td>
                        <td>${mov.codigo_obra}</td>
                        <td>${mov.obra_nome || "-"}</td>
                        <td><span class="badge badge-primary">${
                          mov.tipo
                        }</span></td>
                        <td class="text-right">${formatarMoeda(mov.valor)}</td>
                        <td>${formatarData(mov.data_insercao)}</td>
                    </tr>
                `;
        tbody.innerHTML += row;
      });
    }
  } catch (error) {
    console.error("Erro ao carregar movimentos:", error);
  }
}

function filtrarMovimentos() {
  const competencia = document.getElementById("filtro-competencia").value;
  const codigoObra = document.getElementById("filtro-obra").value;
  carregarMovimentos(competencia, codigoObra);
}

// ================================
// ORÇAMENTO
// ================================

async function carregarOrcamento() {
  try {
    const data = await fetchDados("/orcamento");

    if (data.status === "success") {
      const tbody = document.getElementById("tbody-orcamento");
      tbody.innerHTML = "";

      if (data.data.length === 0) {
        tbody.innerHTML =
          '<tr><td colspan="7" class="text-center">Nenhum orçamento cadastrado</td></tr>';
        return;
      }

      data.data.forEach((orc) => {
        let statusClass = "text-warning";
        let statusText = "📊 Em andamento";

        if (orc.custo_previsto) {
          const percent = (orc.custo_realizado / orc.custo_previsto) * 100;
          if (percent > 100) {
            statusClass = "text-danger";
            statusText = "❌ Acima do orçado";
          } else if (percent > 90) {
            statusClass = "text-warning";
            statusText = "⚠️ Próximo ao limite";
          } else {
            statusClass = "text-success";
            statusText = "✓ Dentro do orçado";
          }
        }

        const desvio = (orc.custo_realizado || 0) - (orc.custo_previsto || 0);
        const percent = orc.custo_previsto
          ? ((orc.custo_realizado || 0) / orc.custo_previsto) * 100
          : 0;

        const row = `
                    <tr>
                        <td>${orc.codigo_obra}</td>
                        <td>${orc.obra_nome || "-"}</td>
                        <td class="text-right">${formatarMoeda(
                          orc.custo_previsto
                        )}</td>
                        <td class="text-right">${formatarMoeda(
                          orc.custo_realizado
                        )}</td>
                        <td class="text-right ${
                          desvio >= 0 ? "text-danger" : "text-success"
                        }">${formatarMoeda(desvio)}</td>
                        <td class="text-right">${percent.toFixed(1)}%</td>
                        <td class="${statusClass}">${statusText}</td>
                    </tr>
                `;
        tbody.innerHTML += row;
      });
    }
  } catch (error) {
    console.error("Erro ao carregar orçamento:", error);
  }
}

document
  .getElementById("btn-editar-orcamento")
  ?.addEventListener("click", function () {
    // Implementar modal de edição de orçamento
    alert("Funcionalidade de edição será implementada em breve");
  });

// ================================
// RELATÓRIOS
// ================================

document
  .getElementById("btn-gerar-relatorio")
  ?.addEventListener("click", async function () {
    const tipo = document.getElementById("tipo-relatorio").value;
    const competencia = document.getElementById("competencia-relatorio").value;

    if (!tipo) {
      mostrarMensagem(
        "#mensagem-relatorio",
        "warning",
        "Selecione um tipo de relatório"
      );
      return;
    }

    mostrarLoading("#mensagem-relatorio");

    try {
      // Implementar geração de relatório
      alert(`Gerando relatório ${tipo} para competência ${competencia}`);
      mostrarMensagem(
        "#mensagem-relatorio",
        "success",
        "Relatório gerado com sucesso!"
      );
    } catch (error) {
      console.error("Erro:", error);
      mostrarMensagem(
        "#mensagem-relatorio",
        "danger",
        "Erro ao gerar relatório"
      );
    }

    esconderLoading("#mensagem-relatorio");
  });

// ================================
// INICIALIZAÇÃO
// ================================

document.addEventListener("DOMContentLoaded", function () {
  console.log("Inicializando Riviera Ingestor...");

  // Carregar dados iniciais
  carregarDashboard();
  carregarMovimentos();
  carregarOrcamento();

  // Auto-refresh a cada 5 minutos
  setInterval(carregarDashboard, 300000);
});
