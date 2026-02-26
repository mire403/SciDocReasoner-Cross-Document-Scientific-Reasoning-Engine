# SciDocReasoner 项目结构

## ✅ 已完成模块

### 1. 文档解析层 (`scidoc_reasoner/ingest/`)
- ✅ `pdf_parser.py` - PDF文档解析器
- ✅ `html_parser.py` - HTML文档解析器（支持arXiv、博客等）
- ✅ `md_parser.py` - Markdown文档解析器

### 2. 预处理层 (`scidoc_reasoner/preprocess/`)
- ✅ `sentence_splitter.py` - 高级句子切分器（处理科学文档特殊格式）
- ✅ `clause_extractor.py` - 语义单元提取（assertion, comparison, causal）

### 3. 抽取层 (`scidoc_reasoner/extraction/`)
- ✅ `entity_extractor.py` - 实体抽取（使用LLM）
- ✅ `claim_extractor.py` - 主张抽取（使用LLM）
- ✅ `hypothesis_detector.py` - 假设检测（使用LLM）

### 4. 链接层 (`scidoc_reasoner/linking/`)
- ✅ `entity_linker.py` - 跨文档实体链接（字符串匹配 + embedding相似度）

### 5. 图构建层 (`scidoc_reasoner/graph/`)
- ✅ `graph_schema.py` - 图模式定义（节点类型、边类型）
- ✅ `graph_builder.py` - 多文档语义推理图构建器

### 6. 推理层 (`scidoc_reasoner/reasoning/`)
- ✅ `hypothesis_inferencer.py` - 假设推断引擎（从相关claims推断新假设）

### 7. 查询层 (`scidoc_reasoner/query/`)
- ✅ `query_engine.py` - 查询引擎，支持4种查询类型：
  1. `query_hypothesis_support` - 查询假设的支持/反驳情况
  2. `query_entity_evolution` - 查询实体的研究演化路径
  3. `query_unvalidated_hypotheses` - 查询未充分验证的假设
  4. `query_claim_relationships` - 查询claim之间的关系

### 8. API层 (`scidoc_reasoner/api/`)
- ✅ `app.py` - FastAPI应用，提供RESTful接口

### 9. 工具层 (`scidoc_reasoner/utils/`)
- ✅ `storage.py` - 结构化数据存储管理

## 📋 核心特性

### ✅ 显式科学推理对象
- Claim（主张）
- Hypothesis（假设）
- Entity（实体）
- Relation（关系：支持、反驳、延伸等）

### ✅ 多文档语义推理图
- 基于NetworkX的图结构
- 节点类型：Document, Entity, Claim, Hypothesis
- 边类型：supports, contradicts, extends, based_on, mentions, contains, links_to

### ✅ 假设推断引擎
- 从相关claims推断新假设
- 使用LLM进行推理
- 支持显式和推断两种来源

### ✅ 结构化存储
- 所有中间结果保存为JSON
- 支持文档、实体、主张、图的持久化

## 🚀 使用方式

### 1. 安装依赖
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. 设置环境变量
创建 `.env` 文件：
```
OPENAI_API_KEY=your_api_key_here
```

### 3. 使用Python API
```python
from scidoc_reasoner.ingest import PDFParser
from scidoc_reasoner.graph import GraphBuilder
from scidoc_reasoner.query import QueryEngine

# 解析文档
parser = PDFParser()
doc = parser.parse("paper.pdf")

# 构建推理图
builder = GraphBuilder()
graph = builder.build_from_documents([doc])

# 查询
engine = QueryEngine(graph)
results = engine.query_hypothesis_support("hypothesis_id")
```

### 4. 使用REST API
```bash
# 启动服务
uvicorn scidoc_reasoner.api.app:app --reload

# 上传文档
curl -X POST "http://localhost:8000/upload/pdf" -F "file=@paper.pdf"

# 处理文档
curl -X POST "http://localhost:8000/process/{doc_id}"

# 构建图
curl -X POST "http://localhost:8000/build_graph" -H "Content-Type: application/json" -d '{"doc_ids": ["doc1", "doc2"]}'

# 查询
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{
  "query_type": "hypothesis_support",
  "parameters": {"hypothesis_text": "..."}
}'
```

## 📝 示例脚本

运行 `example_usage.py` 查看完整使用示例。

## 🎯 项目定位

**SciDocReasoner is not a retrieval system.**
**It is a scientific knowledge evolution model**
**built on explicit semantic reasoning structures.**

## 📊 MVP约束

- ✅ 支持10-30篇论文
- ✅ 所有中间结果结构化保存（JSON）
- ✅ LLM只做判断，不做"记忆"
- ✅ Graph是一等公民
- ✅ 每一步可单独跑、可debug

## 🔮 后续扩展方向

- Temporal hypothesis evolution
- Confidence decay / reinforcement
- Citation-weighted reasoning
- Reviewer-style contradiction detection
