# 🚀 Job Tracker — Busca de Vagas e Análise de Competências

Uma aplicação web desenvolvida em Python que permite buscar oportunidades de emprego, analisar as competências exigidas pelas empresas e organizar vagas de interesse em um único lugar.

## 📌 Sobre o projeto

O Job Tracker foi desenvolvido com o objetivo de tornar o processo de busca por oportunidades profissionais mais organizado e orientado por dados.

Além de reunir vagas de emprego, a aplicação permite analisar as competências mencionadas nas descrições das oportunidades e identificar possíveis lacunas entre os requisitos do mercado e as habilidades cadastradas pelo usuário.

O projeto combina coleta de vagas, processamento de dados, análise de competências, visualização de informações e gerenciamento de oportunidades em um dashboard interativo.

## ✨ Funcionalidades

- **Busca de vagas:** coleta oportunidades de emprego com base nos termos e parâmetros de pesquisa configurados.
- **Análise de competências:** identifica e analisa habilidades profissionais mencionadas nas descrições das vagas.
- **Identificação de lacunas de competências:** compara os requisitos das oportunidades com as habilidades cadastradas pelo usuário.
- **Classificação de requisitos:** organiza as competências conforme sua demanda nas vagas analisadas e prioriza aquelas que o usuário ainda não possui.
- **Dashboard interativo:** apresenta indicadores, resumos analíticos e visualizações dos resultados das buscas.
- **Salvamento de vagas:** permite guardar oportunidades de interesse para consulta posterior.
- **Organização por categorias:** possibilita agrupar vagas salvas, renomear categorias, mover oportunidades entre grupos e remover vagas salvas.
- **Visualização geral das vagas salvas:** permite consultar todas as vagas salvas, independentemente da categoria.
- **Autenticação de usuários:** oferece acesso à aplicação com informações associadas ao usuário.
- **Gerenciamento do catálogo de competências:** permite a administração das habilidades disponíveis para análise.

## 🛠️ Tecnologias utilizadas

| Tecnologia | Aplicação no projeto |
|---|---|
| Python | Lógica da aplicação e processamento de dados |
| Streamlit | Desenvolvimento da interface web e do dashboard |
| Firebase Admin SDK | Integração com os serviços Firebase |
| Cloud Firestore | Armazenamento persistente dos dados |
| Python JobSpy | Coleta de oportunidades de emprego |
| Pandas | Manipulação e processamento de dados |
| Plotly | Criação de gráficos e visualizações interativas |
| python-dotenv | Gerenciamento de variáveis de ambiente |

## 🏗️ Arquitetura do projeto

O projeto possui uma organização modular, separando responsabilidades para facilitar a manutenção e a evolução do código.

```text
job-tracker/
├── config/
├── controllers/
├── models/
├── views/
├── main.py
├── requirements.txt
└── .gitignore
```

- **`config/`** — reúne configurações da aplicação.
- **`controllers/`** — coordena os fluxos da aplicação e as operações de negócio.
- **`models/`** — concentra os modelos de dados e o acesso ao banco de dados.
- **`views/`** — contém os componentes responsáveis pela interface e pela apresentação das informações.
- **`main.py`** — ponto de entrada da aplicação.
- **`requirements.txt`** — lista as dependências Python necessárias para executar o projeto.

A estrutura segue uma organização inspirada no padrão MVC (*Model-View-Controller*), separando a apresentação, a coordenação das operações e o acesso aos dados.

## 🌐 Acesse a aplicação

Você pode acessar o Job Tracker diretamente pelo navegador, sem precisar instalar Python ou configurar o ambiente local.

**[Acessar o Job Tracker](https://job-tracker-axgd7kttydwpay4cqsfaye.streamlit.app/)**

## ⚙️ Como executar o projeto localmente

Para executar o projeto em sua máquina, será necessário instalar as dependências e configurar o acesso ao Firebase.

### Pré-requisitos

- Python instalado em uma versão compatível com as dependências do projeto.
- Git instalado.
- Uma conta Google com acesso ao [Firebase Console](https://console.firebase.google.com/).
- Um projeto Firebase com os serviços e as permissões necessários para a aplicação.

### 1. Clone o repositório

```bash
git clone https://github.com/thayna-data-portfolio/job-tracker.git
cd job-tracker
```

### 2. Crie um ambiente virtual

No Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure as credenciais do Firebase

O projeto utiliza o Firebase Admin SDK para acessar os serviços do Firebase. Para executar a aplicação localmente, você precisará configurar as credenciais de uma conta de serviço.

**Importante:** não basta criar uma conta Google. Você precisa ter acesso a um projeto Firebase com as permissões necessárias. Se não tiver um, será necessário criar um projeto e configurar os serviços utilizados pela aplicação.

#### Como baixar o arquivo JSON

1. Acesse o [Firebase Console](https://console.firebase.google.com/).
2. Selecione o projeto Firebase que será utilizado.
3. Clique na engrenagem ao lado de *Visão geral do projeto* e entre em **Configurações do projeto** (*Project settings*).
4. Abra a aba **Contas de serviço** (*Service accounts*).
5. Na seção do Firebase Admin SDK, selecione a opção para gerar uma nova chave privada (*Generate new private key*).
6. Confirme a operação. Um arquivo JSON será baixado para o seu computador.

O arquivo geralmente possui um nome gerado automaticamente, semelhante a:

```text
nome-do-projeto-firebase-adminsdk-xxxxx.json
```

Esse é o arquivo de credenciais da conta de serviço. Ele contém informações privadas utilizadas para autenticar a aplicação, portanto deve ser tratado como um segredo.

#### Onde colocar o arquivo

Coloque o arquivo JSON na raiz do projeto, no mesmo nível de `main.py`, e renomeie-o para:

```text
serviceAccountKey.json
```

Essa renomeação corresponde à configuração de exemplo utilizada abaixo. Se preferir manter o nome original, ajuste a variável `FIREBASE_CREDENTIALS_PATH` para apontar para o nome correto do arquivo.

### 5. Configure as variáveis de ambiente

Crie um arquivo chamado `.env` na raiz do projeto, no mesmo nível de `main.py`.

Exemplo de conteúdo:

```dotenv
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json
```

Essas variáveis definem o caminho do arquivo de credenciais e parâmetros padrão da aplicação. Confira o código para verificar se há outras variáveis obrigatórias.

A estrutura ficará semelhante a esta:

```text
job-tracker/
├── config/
├── controllers/
├── models/
├── views/
├── .env
├── serviceAccountKey.json
├── main.py
├── requirements.txt
└── .gitignore
```

**Atenção à segurança:** nunca envie o arquivo `serviceAccountKey.json` ou o arquivo `.env` para o GitHub. Verifique se ambos estão incluídos no `.gitignore`. Quem possui acesso à chave privada pode conseguir acessar recursos do projeto Firebase conforme as permissões concedidas à conta de serviço.

### 6. Execute a aplicação

Com o ambiente virtual ativado e as credenciais configuradas, execute:

```bash
python -m streamlit run main.py
```

O Streamlit disponibilizará um endereço local para acessar a aplicação pelo navegador.

## 🔎 Como funciona

1. O usuário acessa a aplicação e realiza a autenticação.
2. Uma busca por oportunidades de emprego é realizada com os parâmetros configurados.
3. As descrições das vagas são processadas para identificar competências e requisitos profissionais.
4. O dashboard apresenta as oportunidades coletadas e os resultados das análises.
5. O usuário pode comparar as competências exigidas com aquelas cadastradas em seu perfil.
6. As oportunidades de interesse podem ser salvas e organizadas em categorias.
7. As vagas salvas podem ser consultadas e gerenciadas posteriormente.

Os resultados das análises dependem das oportunidades retornadas pela coleta, dos termos de pesquisa utilizados e da qualidade das descrições disponíveis.

## 🔐 Configuração e implantação

A aplicação utiliza configurações relacionadas ao Firebase e variáveis de ambiente. Para executá-la em um ambiente de produção, configure as credenciais e os parâmetros necessários diretamente na plataforma de hospedagem.

Na implantação pelo Streamlit Community Cloud, configure os segredos necessários nas configurações da aplicação e garanta que o código esteja preparado para carregá-los corretamente.

## 🎯 Objetivos e aprendizados

O desenvolvimento do Job Tracker envolve conceitos e práticas importantes para aplicações de dados e desenvolvimento de software, como:

- Desenvolvimento de aplicações com Python.
- Criação de dashboards interativos com Streamlit.
- Manipulação e análise de dados com Pandas.
- Visualização de dados com Plotly.
- Integração com banco de dados NoSQL por meio do Cloud Firestore.
- Gerenciamento de configurações e credenciais.
- Organização modular e separação de responsabilidades.
- Extração e análise de competências presentes em descrições de vagas.
- Desenvolvimento de funcionalidades de gerenciamento de dados por usuário.


## 👩‍💻 Autora

**Thayná Lopes**

- [GitHub](https://github.com/thayna-data-portfolio)

---

*Job Tracker é um projeto de portfólio que combina desenvolvimento de software, análise de dados e ferramentas para apoiar a busca por oportunidades profissionais.*
