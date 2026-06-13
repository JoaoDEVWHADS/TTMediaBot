# TTMediaBot

**Olá! Eu sou o João Almeida.** Bem-vindo ao meu fork do **TTMediaBot**, um bot completo de streaming de mídia para o TeamTalk 5. Este repositório é focado em entregar melhorias constantes, estabilidade e novos recursos, como o suporte exclusivo ao YouTube Music.

> 🔗 **Meu Repositório:** [https://github.com/JoaoDEVWHADS/TTMediaBot](https://github.com/JoaoDEVWHADS/TTMediaBot)

---

> **Nota:** Este repositório é um fork do [TTMediaBot original](https://github.com/gumerov-amir/TTMediaBot).

Um bot de streaming de mídia rico em recursos para TeamTalk 5, capaz de reproduzir música de vários serviços (YouTube, YouTube Music, arquivos locais, URLs) com recursos de controle avançados.


## 📋 Diferenciais em relação ao Original

Este fork inclui várias modificações e otimizações:

- **Serviços Removidos:** A integração com o Yandex Music e VK foi removida.
- **Upgrade do SDK do TeamTalk:** Atualizado para o SDK do TeamTalk 5.8.1 para melhor desempenho.
- **Suporte à Arquitetura ARM64:** Adicionado suporte nativo para arquitetura ARM64 (como servidores Raspberry Pi e AWS Graviton) com detecção automática de plataforma e downloads de biblioteca durante a instalação.
  > [!NOTE]
  > Em sistemas `x86_64`, a instalação permanece minimalista e intocada. Em sistemas `ARM`, o instalador e o Dockerfile instalam condicionalmente dependências adicionais (como `libportaudio2`) exigidas pela versão ARM do SDK do TeamTalk para funcionar.
- **Suporte Universal a Distribuições Linux:** O instalador (`ttbotdocker.sh` / `install_git_clone.sh`) agora suporta dinamicamente a configuração automática do Docker e dependências em qualquer distribuição principal (Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux, Raspbian, Arch, etc.) usando o instalador oficial universal e fallbacks de gerenciadores de pacotes dinâmicos para o `jq`.
- **Conteinerização com Docker:** O bot roda em contêineres Docker baseados em Debian 11 e Python 3.10, garantindo compatibilidade com dependências antigas enquanto mantém a estabilidade.
- **Estabilidade Comprovada:** Desde que conheci este bot em 2021, as adaptações feitas para contornar as restrições do YouTube, combinadas com as otimizações de 2021/2022, provaram ser excelentes e confiáveis.

## 🆕 Últimas Atualizações

Para ver o histórico completo de atualizações, incluindo todos os novos recursos, correções de bugs e otimizações, verifique o changelog.

> 📋 **[Ver changelog completo →](CHANGELOG.md)**


## 🎵 Suporte ao YouTube Music

Este fork inclui suporte otimizado para o **YouTube Music** ao lado do YouTube regular:

- **Integração com a API de Busca do YouTube:** Usa a API de Busca do YouTube para uma descoberta de música rápida e confiável.
- **Bibliotecas Otimizadas:** 
  - O YouTube usa `py-yt-search` - uma biblioteca Python rápida e moderna para buscas no YouTube.
  - O YouTube Music usa `ytmusicapi` - a biblioteca oficial da API do YouTube Music.
  - Ambos os serviços usam `yt-dlp` para extração de áudio.
- **Foco em Desempenho:** Projetado para rodar com o mínimo de gargalos, garantindo reprodução suave e resultados de busca rápidos.
- **Sistema Unificado de Cookies:** Tanto o YouTube quanto o YouTube Music usam a mesma configuração de cookies para autenticação.
- **📦 Downloads de Playlists e Álbuns:** Suporte completo para download de coleções inteiras via comando `dlp` com nomenclatura inteligente baseada em metadados.
- **🕵️ Progresso em Tempo Real por PV:** Fique atualizado sobre seus downloads sem poluir o canal.

Alterne entre os serviços usando o comando `sv`:
- `sv yt` - Mudar para o YouTube
- `sv ytm` - Mudar para o YouTube Music

> [!NOTE]
> **Recurso Exclusivo:** O suporte ao YouTube Music é exclusivo deste fork e não está disponível no projeto original do TTMediaBot.

## 🔗 Downloads baseados em links e Armazenamento Local

Este fork inclui um sistema avançado de download baseado em links que permite aos usuários enfileirar links de mídia, listá-los, gerenciá-los e baixá-los sequencialmente ou em arquivos compactados.

### Comandos
- **`aad [link]`**: Adiciona um único link à sua lista.
- **`ad [link1] [link2] ...`**: Adiciona vários links separados por espaço à sua lista.
- **`ld`**: Lista todos os links atualmente na sua lista.
- **`rd [número/link]`**: Remove um link da sua lista por índice ou URL.
- **`ldd [link]`**: Baixa um link diretamente e faz o upload para o canal.
- **`ads`**: Baixa sua lista. Solicita que você selecione:
  - **Opção 1 (Normal):** Baixa cada faixa individualmente e faz o upload para o canal.
  - **Opção 2 (ZIP):** Resolve e compacta todas as faixas em um único arquivo ZIP e depois faz o upload para o canal.
- **`adsc`**: Alterna o **modo de download local** (volátil). Quando ativado:
  - As faixas da lista `ads` são salvas diretamente no sistema de arquivos do VPS em vez de enviadas ao TeamTalk.
  - A Opção 1 salva os arquivos em `data/Downloads/music/` (host: `bots/nomedobot/Downloads/music/`).
  - A Opção 2 salva os arquivos ZIP em `data/Downloads/zips/` (host: `bots/nomedobot/Downloads/zips/`).
  - Os arquivos salvos localmente nunca são excluídos automaticamente.
  - Exibe um relatório final de sucesso/erro após a conclusão.

## 🚀 Instalação Fácil (Recomendado)

Este script instalará automaticamente o Git (se necessário), clonará o repositório e configurará o ambiente Docker.

1.  **Baixe e execute o instalador:**
    ```bash
    wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/install_git_clone.sh
    sudo chmod +x install_git_clone.sh
    sudo ./install_git_clone.sh
    ```

2.  **Monitore o terminal:**
    *   O script instalará automaticamente todas as dependências (incluindo o Docker se necessário).
    *   Fique de olho na saída do terminal para acompanhar o progresso da instalação.
    *   Você pode gerenciar múltiplos bots, atualizar o código e alterar as configurações através do gerenciador do Docker.

---

## ⚙️ Configuração Manual

Se precisar editar manualmente as configurações do bot após a instalação:

1. Os **arquivos de configuração** estão localizados no diretório `bots` dentro da pasta `TTMediaBot` após a configuração inicial.
2. **Faça suas alterações** nos arquivos de configuração conforme necessário.
3. **Reinicie o bot** usando um destes métodos:
   - **Via script do Docker:** Execute `./ttbotdocker.sh`, selecione a opção `2` (Manage Bots) e escolha a opção de reiniciar (geralmente opção `2`).
   - **Via comando do bot:** Envie `rs` como mensagem privada para o bot (requer privilégios de administrador).

---

## 🎮 Comandos

Envie esses comandos para o bot via mensagem privada (PV) ou no canal (se ativado).

### Comandos de Usuário
| Comando | Argumentos | Descrição |
| :--- | :--- | :--- |
| **h** | | Mostra a ajuda dos comandos. |
| **p** | `[busca]` | Reproduz faixas encontradas para a busca. Sem argumento, pausa/retoma. |
| **u** | `[url]` | Reproduz uma transmissão/arquivo a partir de uma URL direta. |
| **s** | | Para a reprodução. |
| **n** | | Reproduz a próxima faixa. |
| **b** | | Reproduz a faixa anterior. |
| **v** | `[0-100]` | Ajusta o volume. Sem argumento mostra o volume atual. |
| **sb** | `[segundos]` | Retrocede a reprodução. Passo padrão se sem argumento. |
| **sf** | `[segundos]` | Avança a reprodução. Passo padrão se sem argumento. |
| **c** | `[número]` | Seleciona uma faixa por número a partir dos resultados de busca. |
| **m** | `[modo]` | Define o modo de reprodução: `SingleTrack`, `RepeatTrack`, `TrackList`, `RepeatTrackList`, `Random`. |
| **sp** | `[0.25-4]` | Define a velocidade de reprodução. |
| **sv** | `[serviço]` | Altera o serviço (ex: `sv yt`, `sv ytm`). |
| **f** | `[+/-][num]` | Gerenciamento de Favoritos. `f` lista. `f +` adiciona a atual. `f -` remove. `f [num]` reproduz. |
| **gl** | | Obtém o link direto para a faixa atual. |
| **dl** | | Baixa a faixa atual e envia para o canal. |
| **dlv** | | Baixa a faixa atual como vídeo e envia para o canal. |
| **dlp** | `[url]` | Baixa todas as faixas de uma playlist/álbum do YouTube, compacta em ZIP e envia para o canal. |
| **aad** | `[link]` | Adiciona um único link/URL à sua lista de downloads customizada. |
| **ad** | `[links]` | Adiciona vários links separados por espaço à lista de downloads. |
| **ld** | | Lista todos os links atualmente na lista de downloads. |
| **rd** | `[número/link]` | Remove um link da lista de downloads pelo índice ou URL. |
| **ldd** | `[link]` | Baixa um link diretamente e envia para o canal do TeamTalk. |
| **ads** | `[1/2]` | Baixa a lista: Opção 1 (Normal sequencial) ou Opção 2 (ZIP compactado). |
| **adsc** | | Alterna o modo de download local: salva os arquivos localmente no VPS em vez de enviá-los. |
| **r** | `[número]` | Reproduz dos Recentes. `r` lista os recentes. |
| **jc** | | Faz o bot entrar no seu canal atual. |
| **qa** | `[busca]` | Adiciona uma faixa à fila de reprodução. |
| **ql** | | Lista todas as faixas atualmente na fila. |
| **qr** | `[número]` | Remove uma faixa específica da fila. |
| **qc** | | Limpa toda a fila de reprodução. |
| **qs** | | Pula a faixa atual e reproduz a próxima da fila imediatamente. |
| **sr** | `[on/off]` | Alterna o Modo de Resultados de Busca. Quando ativo, `p BUSCA` mostra uma lista numerada em vez de tocar imediatamente. Salve com `sc`. |
| **sl** | `[número]` | Seleciona e toca o resultado NÚMERO da última busca feita com o modo `sr` ativo. |
| **slc** | `[número]` | Define quantos resultados são mostrados no modo `sr` (padrão 5). Sem argumento mostra o valor atual. |
| **a** | | Mostra informações sobre o bot. |

### Comandos de Administrador
*Requer privilégios de administrador definidos no `config.json`.*

| Comando | Argumentos | Descrição |
| :--- | :--- | :--- |
| **cg** | `[n/m/f]` | Altera o gênero do bot (neutro, masculino, feminino). |
| **cl** | `[código]` | Altera o idioma (ex: `en`, `ru`, `pt_BR`). |
| **cn** | `[nome]` | Altera o apelido do bot. |
| **cs** | `[texto]` | Altera o texto de status do bot. |
| **cc** | `[r/f]` | Limpa o cache (`r`=recentes, `f`=favoritos). |
| **cm** | | Alterna o envio de mensagens no canal. |
| **ajc** | `[id] [senha]`| Força a entrada em um canal pelo ID. |
| **bc** | `[+/-cmd]` | Bloqueia/Desbloqueia um comando. |
| **l** | | Bloqueia/Desbloqueia o bot (apenas admins podem usar). |
| **ua** | `[+/-user]` | Adiciona/Remove usuários administradores. |
| **ub** | `[+/-user]` | Adiciona/Remove usuários banidos. |
| **eh** | | Alterna o tratamento de eventos internos. |
| **sc** | | Salva a configuração atual no arquivo. |
| **va** | | Alterna a transmissão de voz. |
| **rs** | | Reinicia o bot. |
| **q** | | Fecha/Desliga o bot. |
| **gcid** | | Obtém o ID do canal atual. |

---

## 🐳 Script de Gerenciamento do Docker (`ttbotdocker.sh`)

O script `ttbotdocker.sh` é uma ferramenta abrangente de gerenciamento para o TTMediaBot. Ele fornece uma interface baseada em menus para lidar com todos os aspectos de implantação e gerenciamento de bots.

### Opções do Menu Principal

#### 1. Criar Bot
Cria uma nova instância de bot com um assistente de configuração completo:
- **Nome do bot:** Nome do contêiner e da pasta.
- **Configuração do servidor:** Endereço do servidor, portas TCP/UDP, criptografia.
- **Credenciais:** Usuário e senha.
- **Cookies:** Caminho para o arquivo de cookies do YouTube.
- **Criação em lote:** Cria múltiplos bots de uma vez com numeração automática:
  - Detecta automaticamente números de bots existentes e continua a sequência.
  - Nomes separados para contêineres e apelidos.
  - Evita conflitos no mesmo servidor TeamTalk.

#### 2. Gerenciar Bots
Submenu abrangente de gerenciamento de bots com 12 opções:

**2.1. Iniciar Todos os Bots**
- Inicia todos os contêineres de bots parados.
- Usa filtragem por label do Docker (`role=ttmediabot`).

**2.2. Reiniciar Todos os Bots**
- Para todos os bots (tempo limite de 1 segundo).
- Inicia todos novamente imediatamente.
- Útil para aplicar alterações de configuração.

**2.3. Parar Todos os Bots**
- Para graciosamente todos os bots em execução (tempo limite de 1 segundo).

**2.4. Excluir Bot**
- Menu interativo para selecionar e excluir um único bot.
- Mostra uma lista numerada de todos os bots.
- Remove tanto o contêiner quanto a pasta de configuração.
- Requer confirmação antes da exclusão.

**2.5. Exclusão em Lote de Bots**
- Exclui múltiplos bots em uma única operação.
- Insira números separados por espaço (ex: `1 3 5`).
- Use a opção `0` para **excluir TODOS os bots** simultaneamente.
- Mostra um resumo antes da exclusão com remoção paralela e eficiente.

**2.6. Duplicar Bot**
- Clona a configuração de um bot existente.
- Selecione o bot de origem a partir da lista numerada.
- Mostra o endereço do servidor para cada bot.
- Suporte a duplicação em lote (criar múltiplas cópias).
- Numeração automática para contêineres e solicita explicitamente o **PREFIXO DO APELIDO**.
- Detecção inteligente de conflitos: evita a clonagem se o nome base escolhido já existir.

**2.7. Atualizar Cookies (Todos os Bots)**
- Atualiza os cookies do YouTube para todos os bots de uma só vez.
- Copia o novo arquivo de cookies para todas as pastas de bots.
- Reinicia automaticamente todos os bots para aplicar as alterações.
- Define as permissões corretas do arquivo (1000:1000).

**2.8. Reiniciar com Timer**
- Para todos os bots, aguarda o tempo especificado e depois os inicia.
- Útil para manutenção coordenada do servidor.
- Cronômetro de contagem regressiva visual.
- Tempo especificado em segundos.

**2.9. Atualização de Configuração em Lote**
- Atualiza a configuração para todos os bots simultaneamente.
- Escolha o que atualizar:
  1. Servidor (hostname)
  2. Portas (TCP/UDP)
  3. Criptografia
  4. Credenciais (usuário/senha)
  5. Tudo
- Mostra a configuração atual do primeiro bot.
- Pré-visualização das alterações antes de aplicar.
- Atualiza todos os arquivos `config.json` dos bots.

> [!WARNING]
> **Importante:** Este recurso foi projetado para bots no **mesmo servidor**. Se você tiver bots conectados a vários servidores TeamTalk diferentes, precisará atualizá-los manualmente. Usar este recurso configurará todos os bots com as mesmas configurações de servidor.

**2.10. Backup / Restauração de Bots**
- Utilitário portátil de backup/restauração para a configuração e cache dos bots.
- Salva backups compactados (`.tar.gz`) em um diretório `backups/`.
- A restauração reinstala dinamicamente as configurações dos bots e recria os contêineres Docker.

**2.11. Limpar Todos os Logs dos Bots**
- Utilitário de limpeza rápida que exclui todos os arquivos `*.log` de todas as pastas de dados dos bots para liberar espaço em disco.

**2.12. Retornar ao Menu Principal**

#### 3. Reconstruir Imagem / Atualizar Código
Atualiza o código do bot e reconstrói a imagem do Docker:
- Reconstrói a imagem Docker com `CACHEBUST` para garantir código novo.
- Recria os contêineres com a nova imagem.
- Reinicia apenas os bots que estavam rodando anteriormente.

#### 4. Desinstalar Tudo
Limpeza completa da instalação do TTMediaBot:
- Para todos os contêineres de bots.
- Remove todos os contêineres.
- Exclui todas as pastas de bots.
- Remove a imagem Docker.
- **Aviso:** Esta ação é irreversível!

#### 5. Verificar Atualizações
Verifica automaticamente se há atualizações no repositório do GitHub.
- Usa o `update.sh` para comparar o código local com o repositório remoto.
- Faz backup seguro da configuração antes de atualizar.
- Inclui uma pausa no final para que os usuários possam ler a saída do console.

#### 6. Ativar/Desativar Atualizações Automáticas
Menu dedicado para alternar as atualizações automáticas em segundo plano via mascaramento de serviço do systemd.

#### 7. Limpar Cache do Docker (Não Utilizado)
Ferramenta de limpeza avançada para recuperar espaço em disco sem afetar os bots em execução:
- **Docker Prune:** Remove contêineres parados e imagens não utilizadas.
- **Buildx Cleanup:** Limpa os caches de construção persistentes.
- **Logs do Sistema:** Limpa logs do `journalctl` com mais de 1 dia.
- **Pegada Zero:** Garante que o sistema host permaneça limpo.

#### 8. Sair
Fecha o script.

### Recursos Automáticos

O script faz automaticamente:
- **Verificação de Atualizações** na inicialização se o `update.sh` estiver presente.
- **Instalação de dependências** (Docker, jq) na primeira execução.
- **Construção da imagem Docker** automaticamente e força o PIP a atualizar as bibliotecas (`-U`) em cada reconstrução.
- **Sem prompts de inicialização:** A reconstrução agora é uma opção de menu manual (Opção 3), tornando a inicialização mais rápida.
- **Cria a estrutura do diretório** `bots`.
- **Detecta conflitos** (nomes de contêineres, apelidos no mesmo servidor).
- **Define as permissões** corretamente para os volumes do Docker.
- **Usa labels** para fácil filtragem de contêineres.

---

## 🔄 Script de Atualização Standalone (`update.sh`)

Se você já tem os bots instalados e quer apenas atualizar o código sem usar o gerenciador completo do Docker, pode usar o script independente `update.sh`.

**Como usar:**
1. Baixe o script para sua pasta `TTMediaBot`:
   ```bash
   wget https://raw.githubusercontent.com/JoaoDEVWHADS/TTMediaBot/master/update.sh
   chmod +x update.sh
   ```
2. Execute-o:
   ```bash
   sudo ./update.sh
   ```

Este script atualizará o repositório, reconstruirá a imagem e recriará os contêineres, garantindo que tudo esteja atualizado.

---

## 🍪 Configuração de Cookies do YouTube & YouTube Music

Os cookies são **essenciais** para que o bot reproduza música do **YouTube** e do **YouTube Music** devido a restrições das plataformas.

### Por que os cookies são necessários

O YouTube e o YouTube Music implementaram restrições que exigem autenticação para acessar determinados conteúdos. Os cookies de uma sessão ativa do navegador permitem que o bot contorne essas restrições e reproduza música de ambos os serviços.

### Como obter os cookies

1. **Faça login na sua conta do Google** no seu navegador (Chrome, Edge ou Firefox).

2. **Instale a extensão Get cookies.txt:**
   - Chrome/Edge: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

3. **Acesse o YouTube:** Vá para `youtube.com`.

4. **Exporte os cookies:**
   - Clique no **menu de extensões** do seu navegador.
   - Clique no ícone da extensão **Get cookies.txt LOCALLY**.
   - Clique em **"Export All Cookies"**.
   - Clique no botão **Download**.
   - O navegador pode perguntar onde salvar o arquivo - escolha um local acessível.
   - Caso contrário, o arquivo estará na pasta **Downloads**.

5. **Envie o arquivo** para um local acessível no seu servidor (ex: `/root/cookies.txt`).

### Obtendo o caminho do arquivo de cookies

Ao criar ou atualizar bots, o script solicitará o **caminho absoluto** para o arquivo de cookies. Se você enviou o arquivo para o seu servidor, use este comando para obter o caminho completo:

**Exemplo: se você está no diretório onde enviou o cookies.txt**

```bash
# Navegue até a pasta contendo o cookies.txt
cd /caminho/para/sua/pasta

# Obtenha o caminho completo
pwd
# Saída: /root/meus-cookies

# Ou obtenha o caminho diretamente do arquivo
realpath cookies.txt
# Saída: /root/meus-cookies/cookies.txt
```

**Comando rápido para obter o caminho:**
```bash
echo "$(pwd)/cookies.txt"
# Saída: /root/meus-cookies/cookies.txt
```

Copie este caminho completo e cole quando o script de criação ou atualização do bot solicitar a localização do arquivo de cookies.

> [!IMPORTANT]
> **Nota:** Não use arquivos de cookies muito grandes. Se o arquivo de cookies for muito grande, o yt-dlp pode não reconhecê-lo e o bot não tocará música. Use cookies apenas dos domínios do YouTube/Google.

### Atualizando cookies expirados

Os cookies expiram periodicamente. Quando a reprodução do YouTube parar de funcionar:

1. **Gere novos cookies** seguindo os passos acima.
2. **Atualize todos os bots** usando o script do Docker:
   - Execute `./ttbotdocker.sh`.
   - Selecione a opção `2` (Manage Bots).
   - Selecione a opção `7` (Update Cookies - All Bots).
   - Insira o caminho para o seu novo arquivo de cookies.
   - O script atualizará e reiniciará automaticamente todos os bots.

### Atualização manual de cookies

Alternativamente, atualize os cookies manualmente:
1. Copie o novo `cookies.txt` para cada pasta do bot em `bots/[nome_do_bot]/`.
2. Reinicie o(s) bot(s) afetado(s).

---

## 🌍 Idiomas Suportados

O TTMediaBot suporta múltiplos idiomas. Altere o idioma usando o comando de administrador `cl`.

**Idiomas disponíveis:**
- `ar` - Árabe
- `en` - Inglês
- `es` - Espanhol
- `hu` - Húngaro
- `id` - Indonésio
- `pt_BR` - Português do Brasil
- `ru` - Russo
- `tr` - Turco

**Exemplo:** Envie `cl pt_BR` para mudar o idioma para Português do Brasil.

---

## 🔧 Solução de Problemas

### Bot não reproduz músicas do YouTube

**Sintomas:** O bot se conecta mas não reproduz faixas do YouTube.

**Soluções:**
1. **Verifique os cookies:**
   - Os cookies podem ter expirado.
   - Gere novos cookies e atualize (veja a seção Cookies do YouTube).
   - Verifique o caminho do arquivo de cookies no `config.json`.

2. **Verifique se o arquivo de cookies existe:**
   ```bash
   ls -la bots/[nome_do_bot]/cookies.txt
   ```

3. **Verifique os logs do bot:**
   - **Logs do Docker:**
     ```bash
     docker logs [nome_do_bot]
     ```
   - **Arquivo de log:** Verifique `bots/[nome_do_bot]/TTMediaBot.log` diretamente.

### Bot não conecta ao servidor

**Sintomas:** O bot não aparece online.

**Soluções:**
1. **Verifique os detalhes do servidor:**
   - Verifique o endereço e as portas no `config.json`.
   - Teste a conectividade com o servidor: `ping [endereço_do_servidor]`.

2. **Verifique as credenciais:**
   - Verifique se o usuário/senha estão corretos.
   - Garanta que a conta do bot existe no servidor TeamTalk.

3. **Verifique a configuração de criptografia:**
   - Se o servidor usa criptografia, defina `"encrypted": true` na configuração.
   - **Nota:** O bot busca e confia no certificado SSL do servidor dinamicamente se nenhum certificado CA local (`ttservercert.pem`) for fornecido.

4. **Veja os logs:**
   - **Docker:** `docker logs [nome_do_bot]`
   - **Arquivo:** `bots/[nome_do_bot]/TTMediaBot.log`

### Problemas de Áudio / Sem Som

**Sintomas:** O bot se conecta mas não há som saindo.

**Soluções:**
1. **Verifique o PulseAudio:**
   - O PulseAudio roda dentro do contêiner.
   - Reinicie o bot: `docker restart [nome_do_bot]`.

2. **Verifique o volume:**
   - Envie o comando `v` para verificar o volume atual.
   - Ajuste o volume: `v 50`.

3. **Verifique a configuração de dispositivos de som:**
   - Verifique a seção `sound_devices` no `config.json`.

### O contêiner não inicia

**Sintomas:** O contêiner do Docker fecha imediatamente após iniciar.

**Soluções:**
1. **Verifique os logs:**
   - **Docker:** `docker logs [nome_do_bot]`
   - **Arquivo:** `bots/[nome_do_bot]/TTMediaBot.log`

2. **Verifique a configuração:**
   - Certifique-se de que o `config.json` é um JSON válido.
   - Verifique se há erros de sintaxe.

3. **Recrie o contêiner:**
   - Exclua e recrie o bot usando o `ttbotdocker.sh`.

### Erros de Permissão

**Sintomas:** O bot não consegue ler/gravar arquivos.

**Soluções:**
1. **Corrija as permissões:**
   ```bash
   sudo chown -R 1000:1000 bots/[nome_do_bot]
   ```

2. **Execute o script como root:**
   - Sempre use `sudo ./ttbotdocker.sh`.

---

## ❓ FAQ (Perguntas Frequentes)

### P: Posso rodar múltiplos bots no mesmo servidor?
**R:** Sim! O bot suporta múltiplas instâncias. Use a ferramenta de criação em lote no `ttbotdocker.sh` ou crie os bots individualmente. Cada bot terá seu próprio contêiner e configuração.

### P: Como adiciono mais administradores?
**R:** De duas formas:
- **Via comando:** Envie `ua +nome_do_usuario` para o bot (requer privilégios de administrador).
- **Via config:** Edite `bots/[nome_do_bot]/config.json`, adicione o nome de usuário ao array `teamtalk.users.admins` e reinicie.

### P: Como faço backup das configurações do meu bot?
**R:** Basta copiar todo o diretório `bots`:
```bash
cp -r bots bots_backup_$(date +%Y%m%d)
```

### P: Posso usar os mesmos cookies para todos os bots?
**R:** Sim! Use o recurso "Update Cookies (All Bots)" no menu de gerenciamento para aplicar o mesmo arquivo de cookies a todos os bots de uma vez.

### P: O bot fica se desconectando. O que devo fazer?
**R:** Verifique:
- A estabilidade da sua rede.
- O status do servidor.
- Os logs do bot: `docker logs [nome_do_bot]` ou `bots/[nome_do_bot]/TTMediaBot.log`.
- Aumente o `reconnection_timeout` no `config.json`.

### P: Como altero o apelido do bot?
**R:** De duas formas:
- **Via comando:** Envie `cn NovoApelido` (apenas administradores).
- **Via config:** Edite `teamtalk.nickname` no `config.json` e reinicie.

### P: Posso rodar bots em servidores TeamTalk diferentes?
**R:** Com certeza! Cada contêiner de bot pode se conectar a um servidor diferente. Basta especificar os endereços dos servidores durante a criação ou na configuração.

### P: Quantos recursos cada bot consome?
**R:** Cada contêiner de bot usa aproximadamente:
- **RAM:** 100-200 MB (ocioso), 200-400 MB (reproduzindo).
- **CPU:** Mínimo quando ocioso, moderado ao transcodificar áudio.
- **Disco:** ~500 MB por bot (incluindo dependências).

### P: O que acontece se eu atualizar o código do repositório?
**R:** Suas configurações dos bots no diretório `bots` serão preservadas. Após baixar as atualizações:
1. Reconstrua a imagem Docker: `docker build -t ttmediabot .`
2. Recrie os contêineres usando a função de recriação do script.

---

## 📊 Logs e Monitoramento

### Visualizando Logs em Tempo Real

**Para um bot específico:**
```bash
docker logs -f [nome_do_bot]
```

**Para todos os bots:**
```bash
docker logs -f $(docker ps -q -f "label=role=ttmediabot")
```

### Localização dos Arquivos de Log

Cada bot armazena logs em seu respectivo diretório:
```
bots/[nome_do_bot]/TTMediaBot.log
```

### Configuração de Logs

Edite as configurações de log no `config.json`:

```json
"logger": {
    "log": true,
    "level": "INFO",
    "format": "%(levelname)s [%(asctime)s]: %(message)s",
    "mode": "FILE",
    "file_name": "TTMediaBot.log",
    "max_file_size": 0,
    "backup_count": 0
}
```

**Níveis de log:**
- `DEBUG` - Informações detalhadas para diagnosticar problemas.
- `INFO` - Mensagens informativas gerais (padrão).
- `WARNING` - Mensagens de aviso.
- `ERROR` - Apenas mensagens de erro.

**Ativar log de depuração (debug):**
Altere `"level": "INFO"` para `"level": "DEBUG"` e reinicie o bot.

### Monitorando o Status do Bot

**Ver contêineres rodando:**
```bash
docker ps -f "label=role=ttmediabot"
```

**Ver todos os contêineres (incluindo parados):**
```bash
docker ps -a -f "label=role=ttmediabot"
```

**Ver uso de recursos:**
```bash
docker stats $(docker ps -q -f "label=role=ttmediabot")
```
