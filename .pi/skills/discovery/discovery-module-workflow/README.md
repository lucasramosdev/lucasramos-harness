# 🚀 Claude Code Skill: Discovery & Backlog Workflow

Este workflow automatiza o processo de *Discovery* visual e a criação de *Backlog* no GitHub. Ele analisa mockups/imagens de um módulo, levanta requisitos funcionais e não funcionais, gera um PRD e orquestra a criação de Épicos e Issues (Frontend/Backend) diretamente no repositório, incluindo estimativas PERT.

## 📋 Funcionalidades

O fluxo é rigorosamente dividido em 3 fases:

1. **Validação:** Checa se o diretório do módulo existe e possui imagens válidas de UI/UX.
2. **Geração de PRD:** Utiliza a skill `/create-prd` cruzando a interface com boas práticas de engenharia para gerar um arquivo `prd-[NOME_DO_MODULO].md`.
3. **Orquestração via GitHub MCP:**
   - Cria um **Épico** no repositório com o resumo do PRD.
   - Cria as **Issues filhas** (técnicas) vinculadas ao Épico.
   - Calcula a estimativa de esforço de cada tarefa usando a **Técnica PERT** (Otimista, Realista, Pessimista).
   - Adiciona as labels necessárias para que o GitHub Projects puxe as tarefas automaticamente para o Board.

---

## ⚙️ Pré-requisitos

Para que a automação funcione de ponta a ponta sem erros, garanta que seu ambiente e repositório estejam configurados:

### 1. Estrutura de Pastas
As imagens de referência da UI devem ser colocadas no seguinte caminho antes de rodar o comando:
`/discovery/modules/[NOME_DO_MODULO]/`

### 2. Ferramentas Locais
- **Claude Code** instalado e autenticado.
- Servidor **GitHub MCP padrão** configurado no Claude Code (necessário para a ferramenta `create_issue`).
- Arquivo `discovery-workflow.md` salvo no projeto (ex: `.claude/commands/discovery-workflow.md`).

### 3. Configuração no GitHub (Repositório)
As seguintes *Labels* precisam estar criadas previamente no repositório de destino:
- `auto-board` (Usada pela automação do GitHub Projects)
- `epic`
- `frontend`
- `backend`

### 4. Configuração no GitHub (Projects Board)
No seu Board (`https://github.com/orgs/HeluApp/projects/2`), configure um **Workflow de Auto-add**:
- **Filtro:** `is:issue label:auto-board`
Isso garante que toda issue criada pelo Claude caia diretamente na coluna inicial do seu Kanban.

---

## 🚀 Como Usar

### Opção 1: Via Terminal (Recomendado)
Se você configurou a função/alias no seu `~/.bashrc` ou `~/.zshrc`:

```bash
# Sintaxe: discovery <nome-do-modulo> <nome-do-repositorio>
discovery pagamentos api-helu