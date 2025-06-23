# n8n 工作流生成器自定义节点

这是一个用于 n8n 的自定义节点项目，它允许用户通过自然语言描述来生成和部署 n8n 工作流。核心功能是利用大型语言模型（LLM）将自然语言指令转换为可执行的 n8n 工作流 JSON 配置，并通过 n8n API 自动部署。

## 新增与优化说明

- **simple_auto_generator.py**  
  用于替代和完善原有的 n8n_generator.py，支持更强的节点类型别名映射、参数过滤、自动修正、合规性兜底、动态提示词拼接等。是当前推荐的主力自动化生成脚本。

- **node_config.json**  
  收录 n8n 官方节点参数结构，作为所有自动生成和校验的唯一规范源。所有节点参数过滤、修正、合规性校验均以此为准。

- **test_n8n_auth.py**  
  用于 n8n API 认证与连通性测试，帮助快速定位 API Key、网络、权限等问题。

- **test_simple_generator.py**  
  用于自动化测试 simple_auto_generator.py 的流程生成与部署能力，便于开发调试和回归测试。

### 工作流自动生成与合规性

- **Python 端（simple_auto_generator.py）**  
  - 支持绝对路径加载 node_config.json，兼容 TS 端和本地调用。
  - 输出自动加上 `JSON_RESULT_START`/`JSON_RESULT_END` 标记，便于 TS 端稳健提取 JSON。
  - 自动修正 set 节点 values 结构、writeBinaryFile 参数名等，确保生成的 workflow JSON 严格符合 n8n 官方导出格式。
  - 支持动态拼接 node_config.json 参数名到大模型提示词，提升 LLM 输出合规性。

- **TypeScript 端（src/WorkflowGenerator.node.ts）**  
  - 增加详细日志，关键步骤（参数获取、Python 输出、JSON 解析、异常）均有输出，便于排查问题。
  - 输出清洗逻辑：优先提取 `JSON_RESULT_START ... JSON_RESULT_END` 之间内容，自动展开数组，保证 n8n 能正确识别。
  - 支持 continueOnFail，异常时输出详细错误信息。

### 使用建议

- **务必保证 python 目录下有 node_config.json，且内容为最新 n8n 官方节点参数结构。**
- **推荐始终用 simple_auto_generator.py 作为主入口，n8n_generator.py 仅供参考或兼容老流程。**
- **如需自定义节点类型、参数规范，直接修改 node_config.json 并重启服务。**

### 常见问题与排查

- **流程为空/节点不显示**：多为 node_config.json 缺失、节点 type 拼写错误、set.values 结构不合规等。请检查 Python 日志和 TS 端日志。
- **propertyValues[itemName] is not iterable**：set 节点 values 字段结构错误，需为对象（string/number/boolean/array），不能为数组。
- **WriteBinaryFile 报 Buffer.from(undefined)**：上游节点未正确输出 binary 字段，或 dataPropertyName 配置不一致。
- **找不到 node_config.json**：请确保 py 端用绝对路径加载，或 TS 端 spawn py 时指定 cwd。

### 贡献与维护

- 所有节点参数、类型、结构请以 node_config.json 为唯一标准，保持与 n8n 官方导出格式完全一致。
- 如需扩展节点类型或参数，建议先在 n8n 页面手动配置并导出，再同步到 node_config.json。

## 核心组件

本项目主要由以下几个关键部分组成：

*   \`src/WorkflowGenerator.node.ts\`: 这是 n8n 自定义节点的 TypeScript 源代码。它定义了节点在 n8n 中的显示、输入、输出和执行逻辑。此节点负责调用后端的 Python 脚本，并处理其输出。
*   \`python/n8n_generator.py\`: 这是一个 Python 脚本，包含了与大型语言模型（如 DeepSeek 或 OpenRouter）交互的逻辑，用于根据自然语言描述生成 n8n 工作流的 JSON 配置，并负责将生成的配置部署到 n8n 实例。
*   \`python/config.py\`: 包含了 LLM API 密钥、API 基础 URL 以及 n8n 实例的 URL 和 API 密钥等敏感配置信息。
*   \`python/requirements.txt\`: 列出了 `n8n_generator.py` 脚本所需的所有 Python 依赖包。
*   \`package.json\` 和 \`tsconfig.json\`: Node.js 项目的配置文件，用于管理依赖、定义构建脚本和配置 TypeScript 编译选项。

## 先决条件

在开始之前，请确保你的系统满足以下条件：

*   **Git**: 用于克隆本仓库。
*   **Node.js 和 npm (或 Yarn)**: 用于编译 TypeScript 节点和管理 Node.js 依赖。推荐使用 Node.js 16 或更高版本。
*   **Python 3.8+**: 用于运行工作流生成脚本。强烈推荐使用 Conda (Miniconda/Anaconda) 来管理 Python 环境。
*   **Conda (Miniconda/Anaconda)**: 用于创建和管理独立的 Python 环境。
*   **n8n 实例**: 一个运行中的 n8n 实例（可以是本地安装、Docker 或云服务），你需要其 API 访问权限。

## 环境设置

### 1. 克隆仓库

首先，将本仓库克隆到你的本地机器：

```bash
git clone <你的仓库URL>
cd python_node
```

### 2. Python (Conda) 环境配置

本项目的 Python 部分依赖于特定的库。为了避免依赖冲突，我们强烈建议使用 Conda 创建一个独立的虚拟环境。

1.  **创建 Conda 环境**:
    ```bash
    conda create -n ai-agent-n8n python=3.9 # 你可以使用其他Python版本，但推荐3.8+
    ```

2.  **激活 Conda 环境**:
    ```bash
    conda activate ai-agent-n8n
    ```
    激活后，你的终端提示符前应该会显示 `(ai-agent-n8n)`。

3.  **安装 Python 依赖**:
    在激活的环境中，安装 `python/requirements.txt` 中列出的所有依赖：
    ```bash
    pip install -r python/requirements.txt
    ```

4.  **配置 `python/config.py`**:
    打开 `python/config.py` 文件，并填写你的 API 密钥和 URL。

    ```python
    # python/config.py
    OPENROUTER_CONFIG = {
        "api_key": "YOUR_OPENROUTER_API_KEY", # 替换为你的 OpenRouter/DeepSeek API Key
        "api_base": "https://openrouter.ai/api/v1", # 如果是 DeepSeek，可能是 https://api.deepseek.com/v1
        "model": "deepseek-chat" # 或你的模型名称，例如 'deepseek-coder'
    }

    N8N_CONFIG = {
        "base_url": "http://localhost:5678", # 替换为你的 n8n 实例的 Base URL
        "api_key": "YOUR_N8N_API_KEY" # 替换为你的 n8n API Key
    }
    ```
    *   **获取 n8n API Key**: 在 n8n 界面中，点击右上角的用户头像 -> `My Profile` -> `API Keys` -> `New API Key`。

### 3. TypeScript/Node.js 环境配置

1.  **安装 Node.js 依赖**:
    在项目根目录 (`python_node`) 下，安装所有 Node.js 依赖：
    ```bash
    npm install
    # 或者如果你使用 Yarn
    # yarn install
    ```

### 4. n8n API 凭证配置

为了让 `WorkflowGenerator` 节点能够部署工作流到你的 n8n 实例，你需要在 n8n 中创建一个 `n8n API` 凭证。

1.  **登录你的 n8n 实例。**
2.  在左侧导航栏中，点击 **`Credentials`**。
3.  点击 **`New Credential`**。
4.  搜索并选择 **`n8n API`** 凭证类型。
5.  **填写凭证详情**:
    *   **Credential Name**: 给你的凭证起一个有意义的名字，例如 `My N8N Instance`。
    *   **Base URL**: 填写你的 n8n 实例的 URL (例如：`http://localhost:5678`)。
    *   **API Key**: 填写你在 `python/config.py` 中使用的 n8n API Key。
6.  点击 **`Save`**。

## 构建与链接 n8n 节点

完成环境设置后，你需要编译 TypeScript 节点，并将其链接到你的 n8n 安装目录，以便 n8n 能够发现并加载它。

1.  **编译 TypeScript 代码**:
    在项目根目录 (`python_node`) 中执行：
    ```bash
    npm run build
    ```
    这会将 TypeScript 代码编译成 JavaScript 文件，并放置在 `dist` 目录下。

2.  **将节点链接到你的 n8n 目录**:
    *   **在自定义节点项目目录中执行 `npm link`**:
        ```bash
        cd D:\typescript_code\python_node # 确保当前在你的项目根目录
        npm link
        ```
        这会创建一个指向你当前项目 (`n8n-workflow-generate`) 的全局符号链接。

    *   **在 n8n 安装目录中执行 `npm link <your-node-package-name>`**:
        首先，找到你的 n8n 安装目录。对于 Windows 用户，如果你是全局安装的 n8n，它通常位于 `C:\Users\<你的用户名>\.n8n`。
        ```bash
        cd C:\Users\liangwei\.n8n # 替换为你的 n8n 数据目录
        npm link n8n-workflow-generate
        ```
        这条命令会指示 n8n 在其 `custom/node_modules` 目录下创建一个符号链接，指向你自定义节点的编译输出。

3.  **重启 n8n 实例**:
    完成链接后，**务必重启你的 n8n 实例**。这是让 n8n 识别并加载新自定义节点的关键步骤。

## 在 n8n 中使用节点

节点成功链接并重启 n8n 后，你就可以在工作流中使用 `WorkflowGenerator` 节点了。以下是构建一个基础工作流的步骤：

### 基础工作流流程：`Set` -> `Code` -> `WorkflowGenerator`

这个流程将模拟一个自然语言输入，通过 `Code` 节点提取，然后传递给 `WorkflowGenerator` 节点进行处理。

1.  **打开 n8n 工作流编辑器。**
2.  **创建新工作流** 或 **编辑现有工作流**。

### 1. 配置 `Set` 节点

*   **添加节点**: 在画布上点击 `Add new node` (大加号图标) 或按空格键，搜索并选择 `Set` 节点。
*   **节点参数**:
    *   **Keep Only Set**: 确保设置为 `false`。
    *   **Values**: 点击 `Add Value`。
        *   **Type**: `String`
        *   **Value**: 输入包含你自然语言描述的 JSON 字符串。
            ```json
            {
              "data": {
                "content": "请生成一个工作流，该工作流将使用 HTTP Request 节点发送 GET 请求到 URL \"https://jsonplaceholder.typicode.com/posts/1\"，并将响应内容保存到名为 \"api_response.json\" 的文件中。"
              }
            }
            ```
            你可以将 `content` 字段中的自然语言描述替换为你想要生成的工作流内容。

### 2. 配置 `Code` 节点

*   **连接节点**: 从 `Set` 节点的输出连接到 `Code` 节点的输入。
*   **添加节点**: 搜索并选择 `Code` 节点。
*   **节点参数**:
    *   **Input Handling (输入处理)**: 选择 `Run Once for All Items`。
    *   **JavaScript Code**: 粘贴以下代码。这段代码负责从上一个 `Set` 节点模拟的 JSON 输入中提取自然语言描述。
        ```javascript
        const items = [];
        // 使用 $input.all() 获取所有输入项，它会返回一个数组
        for (const item of $input.all()) {
            // 获取当前项的 JSON 数据
            const jsonData = item.json;
            if (jsonData.data && jsonData.data.content) {
                items.push({ json: { naturalLanguage: jsonData.data.content } });
            } else {
                console.log("输入项缺少 'data.content' 字段:", jsonData);
            }
        }
        return items;
        ```

### 3. 配置 `WorkflowGenerator` 节点

*   **连接节点**: 从 `Code` 节点的输出连接到 `WorkflowGenerator` 节点的输入。
*   **添加节点**: 搜索并选择 `Workflow Generator` 节点。
*   **节点参数**:
    *   **Credential to connect with**: 从下拉菜单中选择你在 `n8n API 凭证配置` 步骤中创建的 n8n API 凭证（例如：`My N8N Instance`）。
    *   **Operation (操作)**: 选择 `Generate Workflow`。
    *   **Workflow Description (工作流描述)**:
        *   点击输入框右侧的齿轮图标或直接在输入框中输入表达式。
        *   输入表达式：`{{ $json.naturalLanguage }}`
        *   这个表达式会将 `Code` 节点输出的 `naturalLanguage` 字段值作为输入传递给 `WorkflowGenerator` 节点。

### 运行工作流

完成所有节点的配置和连接后，你可以点击工作流画布顶部的 `Execute Workflow` 按钮来运行整个工作流。

*   如果一切顺利，`WorkflowGenerator` 节点将成功调用 Python 脚本，并根据你提供的自然语言描述在你的 n8n 实例中生成并部署一个新的工作流。
*   新生成的工作流会显示在你的 n8n 工作流列表中。

## 项目结构

```
.
├── dist/                          # 编译后的 JavaScript 文件
├── nodes/                         # n8n 自定义节点定义文件 (通常用于发布)
├── python/
│   ├── config.py                  # Python 配置 (API Keys, URLs)
│   ├── n8n_generator.py           # 核心 Python 脚本 (LLM交互, 工作流生成与部署)
│   └── requirements.txt           # Python 依赖列表
├── src/
│   ├── WorkflowGenerator.node.ts  # n8n 自定义节点 TypeScript 源代码
│   └── ...                        # 其他 TypeScript 源代码
├── .eslintrc.js                   # ESLint 配置
├── .gitignore                     # Git 忽略文件
├── .prettierrc                    # Prettier 配置
├── gulpfile.js                    # Gulp 构建任务
├── package.json                   # Node.js 项目元数据和脚本
├── tsconfig.json                  # TypeScript 编译器配置
└── README.md                      # 本文件
```

## 常见问题与故障排除

*   **`ModuleNotFoundError: No module named 'openai'`**:
    *   确保你已激活正确的 Conda 环境 (`conda activate ai-agent-n8n`)。
    *   在激活的环境中运行 `pip install -r python/requirements.txt`。
    *   检查 `src/WorkflowGenerator.node.ts` 中 `spawn` 函数调用的 Python 解释器路径是否正确（确保指向你的 Conda 环境中的 `python.exe`）。
*   **`SyntaxError: f-string: unmatched '('`**:
    *   这通常是 Python f-string 内部引号或括号转义问题。我们已尝试通过删除相关日志解决，如果再次出现，请检查 `n8n_generator.py` 中最新的 f-string 语法。
*   **`NodeOperationError: Failed to parse Python script output as JSON`**:
    *   这表示 Python 脚本的标准输出中包含了非 JSON 的内容。
    *   确保 `python/n8n_generator.py` 中只有最终的 JSON 结果通过 `print(json.dumps(...))` 输出到标准输出。
    *   检查所有 `logger.info` 和 `logger.warning` 都已重定向到 `sys.stderr`。
    *   重新检查 n8n 终端输出，看是否有其他意外的文本。
*   **节点在 n8n 中不可见**:
    *   确认已成功执行 `npm link` 和 `npm link n8n-workflow-generate`。
    *   确保 n8n 实例已重启。
    *   尝试清除浏览器缓存。
    *   检查 n8n 启动日志，看是否有任何关于加载节点的错误或警告。

## 提交到 GitHub

在提交到 GitHub 时，请忽略敏感配置文件（例如 python/config.py），并参考 python/config.py.example 文件。具体步骤如下：

1. 在项目根目录下创建（或修改） .gitignore 文件，确保忽略以下文件或目录：
   - dist/（编译产物）
   - node_modules/（Node.js 依赖）
   - python/config.py（敏感配置文件，包含 API 密钥）
   - .idea/、.vscode/（IDE 配置）
   - *.log、npm-debug.log*、yarn-error.log*（日志文件）
   - *.tgz、__pycache__/（其他临时文件）

2. 将 python/config.py.example 文件（或类似模板）提交到仓库，方便用户参考。

3. 使用 Git 命令（例如 git add、git commit、git push）将项目提交到 GitHub。

## 变更记录

- 2024-06-XX：节点配置文件已由 base_node.json 更名为 node_config.json，所有相关代码、日志、注释已同步更新。

## 如何通过源码自动生成 node_config.json

本项目的 node_config.json 文件并非手工维护，而是通过自动化脚本批量从 n8n 官方节点源码中提取生成，确保参数结构与官方节点完全一致。

**自动生成流程如下：**

1. **遍历 n8n-spec-source 源码目录**
   - 脚本会递归遍历 `n8n-spec-source/nodes` 目录，定位所有官方节点的 TypeScript 源码（如 `Kafka.node.ts`、`Set.node.ts` 等）和 JSON 元数据文件。

2. **解析 TypeScript/JSON 节点定义**
   - 对于每个节点，自动分析其 `displayName`、`type`、`group`、`version`、`description`、`inputs`、`outputs`、`credentials`、`properties` 等核心字段。
   - 对于 `properties` 字段，支持递归解析嵌套结构、分组、类型选项、依赖关系等，确保参数定义完整。

3. **结构化整理所有节点参数**
   - 将所有节点的参数结构统一整理为标准 JSON 格式，便于 LLM 理解和推理。
   - 自动去重、合并多版本节点，避免冗余。

4. **批量写入 node_config.json**
   - 最终将所有节点的参数结构批量写入 `python/node_config.json`，作为 LLM 自动生成 n8n 工作流的唯一规范源。

**优势：**
- 保证参数结构与 n8n 官方节点完全一致，避免人工维护出错。
- 支持批量扩展、自动更新，适配 n8n 节点库升级。
- LLM 训练和推理时可直接引用，极大提升自动生成流程的准确性和合规性。

如需自定义节点或参数规范，只需扩展源码解析脚本或手动补充 node_config.json 即可。