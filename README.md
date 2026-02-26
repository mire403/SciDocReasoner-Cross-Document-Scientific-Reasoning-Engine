<div align="center">



</div>

<div align="center">

**跨文档科学推理引擎** | **不是检索系统，是科学知识演化模型**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAI](https://img.shields.io/badge/LLM-OpenAI-orange.svg)](https://openai.com/)

**从大量科研文档中显式建模「主张—假设—证据」，进行跨文档因果链与知识演化推理**

[快速开始](#-快速开始) • [架构设计](#-系统架构) • [功能特性](#-核心功能) • [API文档](#-api接口) • [示例代码](#-代码示例)

</div>

---

## 📖 项目简介

### 🎯 我们不是在做...

❌ **多篇论文拼接 summary** - 不是简单的文本拼接  
❌ **单文档 QA** - 不是问答系统  
❌ **向量检索 + LLM 编答案** - 不是检索增强生成  
❌ **隐式 reasoning** - 不是在 prompt 里"想一想"就完事  

### ✅ 我们在构建...

**SciDocReasoner** 是一个**显式的科学知识演化推理系统**，它能够：

1. **结构化建模** 📊
   - 从论文中提取**主张（Claim）**、**假设（Hypothesis）**、**证据（Evidence）**
   - 构建**多文档语义推理图**，而非简单的文本索引

2. **跨文档推理** 🔗
   - 识别不同论文中的**共享实体**
   - 发现**冲突主张**和**知识演化关系**
   - 推断**未被明确陈述的假设**

3. **图上的推理** 🕸️
   - 推理在**图结构**上进行，而非仅在 LLM 的 prompt 中
   - LLM 只负责：抽取、判断关系、推断新假设
   - Graph 是一等公民，所有推理可追溯、可调试

### 🌟 核心价值

> **SciDocReasoner is not a retrieval system.**  
> **It is a scientific knowledge evolution model**  
> **built on explicit semantic reasoning structures.**

---

## 🏗️ 系统架构

### 📐 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Documents Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │   PDF    │  │   HTML   │  │    MD    │                    │
│  └──────────┘  └──────────┘  └──────────┘                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Document Parser Layer                            │
│  • PDF Parser  • HTML Parser  • Markdown Parser             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           Preprocessing Layer                                 │
│  • Sentence Splitter  • Clause Extractor                    │
│  (科学语义最小单元切分)                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Extraction Layer (LLM-powered)                    │
│  • Entity Extractor  • Claim Extractor  • Hypothesis Detector│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            Linking Layer                                      │
│  • Cross-Document Entity Linker                             │
│  (字符串匹配 + Embedding 相似度)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Semantic Reasoning Graph                             │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐            │
│  │Document  │─────▶│ Entity   │─────▶│  Claim   │            │
│  └──────────┘      └──────────┘      └──────────┘            │
│       │                 │                 │                  │
│       └─────────────────┴─────────────────┘                  │
│                           │                                  │
│                           ▼                                  │
│                    ┌──────────┐                             │
│                    │Hypothesis│                             │
│                    └──────────┘                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Hypothesis Inference Engine                           │
│  (从相关 claims 推断新假设)                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Engine                                     │
│  • Hypothesis Support  • Entity Evolution                     │
│  • Unvalidated Hypotheses  • Claim Relationships            │
└─────────────────────────────────────────────────────────────┘
```

### 🧩 模块详解

#### 1️⃣ 文档解析层 (`ingest/`)

**功能**：将不同格式的文档解析为统一的结构化格式

```python
from scidoc_reasoner.ingest import PDFParser, HTMLParser, MDParser

# PDF 解析
pdf_parser = PDFParser()
doc = pdf_parser.parse("paper.pdf")
# 输出: ParsedDocument(doc_id, title, authors, sections, ...)

# HTML 解析（支持 arXiv、博客等）
html_parser = HTMLParser()
doc = html_parser.parse("arxiv_paper.html")

# Markdown 解析
md_parser = MDParser()
doc = md_parser.parse("survey.md")
```

**深度解析**：
- 自动识别文档章节（Abstract, Introduction, Methods, Results, Discussion）
- 提取元数据（标题、作者、创建日期）
- 生成唯一文档 ID（基于文件哈希）
- 输出统一格式，便于后续处理

#### 2️⃣ 预处理层 (`preprocess/`)

**功能**：将文档切分为科学语义最小单元

```python
from scidoc_reasoner.preprocess import SentenceSplitter, ClauseExtractor

# 高级句子切分（处理科学文档特殊格式）
splitter = SentenceSplitter()
sections = [
    {"section": "Results", "raw_text": "...", "sentences": [...]}
]
sentences = splitter.split_document(doc_id, sections)

# 语义单元提取
extractor = ClauseExtractor()
clauses = extractor.extract_clauses(sentences)
# 识别: assertion, comparison, causal, other
```

**深度解析**：
- **句子切分**：处理科学符号、引用、缩写（如 "e.g.", "Fig. 1", "BERT"）
- **语义单元**：识别断言、比较、因果关系的句子
- 每个句子包含元数据：`sentence_id`, `section`, `doc_id`, `position`

#### 3️⃣ 抽取层 (`extraction/`) 🧠

**功能**：使用 LLM 提取实体、主张、假设

```python
from scidoc_reasoner.extraction import (
    EntityExtractor, ClaimExtractor, HypothesisDetector
)

# 实体抽取
entity_extractor = EntityExtractor()
entities = entity_extractor.extract_entities(sentences)
# 实体类型: model, method, dataset, metric, biological, chemical, other

# 主张抽取
claim_extractor = ClaimExtractor()
claims = claim_extractor.extract_claims(sentences, entities)
# 主张类型: comparative, causal, conclusive, other
# 示例: "Method A outperforms Method B on dataset X"

# 假设检测
hypothesis_detector = HypothesisDetector()
hypotheses = hypothesis_detector.detect_hypotheses(sentences, claims)
# 检测显式假设（如 "we hypothesize that..."）
```

**深度解析**：
- **批量处理**：将句子分批处理，避免 token 限制
- **结构化输出**：LLM 返回 JSON 格式，包含置信度分数
- **实体关联**：主张自动关联到提及的实体
- **置信度评分**：每个抽取结果都有置信度（0.0-1.0）

**LLM Prompt 示例**（实体抽取）：
```
Extract scientific entities from the following sentences. 
For each entity, identify:
1. The entity name/text
2. Entity type: one of ["model", "method", "dataset", "metric", ...]
3. The sentence number where it appears

Return a JSON array of entities.
```

#### 4️⃣ 链接层 (`linking/`) 🔗

**功能**：跨文档实体链接，识别不同论文中的同一实体

```python
from scidoc_reasoner.linking import EntityLinker

linker = EntityLinker(model_name="all-MiniLM-L6-v2")
entity_links = linker.link_entities(all_entities)
# 返回: {"Transformer": ["ent_1", "ent_5", "ent_12"], ...}
```

**深度解析**：
- **字符串匹配**：精确匹配、模糊匹配（处理缩写、别名）
- **Embedding 相似度**：使用 sentence-transformers 计算语义相似度
- **类型约束**：只链接相同类型的实体（model 只链接 model）
- **阈值控制**：可调节相似度阈值（默认 0.75）

**链接策略**：
1. 精确字符串匹配
2. 子串匹配（"BERT" vs "Bidirectional Encoder Representations from Transformers"）
3. 词重叠度 > 60%
4. Embedding 余弦相似度 > 阈值

#### 5️⃣ 图构建层 (`graph/`) 🕸️

**功能**：构建多文档语义推理图

```python
from scidoc_reasoner.graph import GraphBuilder, NodeType, EdgeType

builder = GraphBuilder()
graph = builder.build_from_documents(
    documents=all_documents,
    entities=all_entities,
    claims=all_claims,
    hypotheses=all_hypotheses,
    entity_links=entity_links
)

# 图结构
# 节点类型: Document, Entity, Claim, Hypothesis
# 边类型: supports, contradicts, extends, based_on, mentions, contains, links_to
```

**深度解析**：

**节点类型**：
- `Document`: 文档节点，包含标题、作者、摘要
- `Entity`: 实体节点，包含文本、类型、上下文
- `Claim`: 主张节点，包含文本、类型、置信度
- `Hypothesis`: 假设节点，包含文本、置信度、来源（explicit/inferred）

**边类型**：
- `supports`: Claim → Hypothesis（主张支持假设）
- `contradicts`: Claim → Claim/Hypothesis（主张反驳）
- `extends`: Claim → Claim（主张延伸）
- `based_on`: Entity/Claim → Hypothesis/Claim（基于证据）
- `mentions`: Claim/Document → Entity（提及实体）
- `contains`: Document → Claim/Entity/Hypothesis（文档包含）
- `links_to`: Entity → Entity（跨文档实体链接）

**图构建逻辑**：
```python
# 1. 添加文档节点
for doc in documents:
    graph.add_node(f"doc_{doc_id}", node_type=NodeType.DOCUMENT, ...)

# 2. 添加实体节点并链接
for entity in entities:
    graph.add_node(f"ent_{entity_id}", node_type=NodeType.ENTITY, ...)
    # 跨文档链接
    if entity_linked:
        graph.add_edge(ent1, ent2, edge_type=EdgeType.LINKS_TO)

# 3. 添加主张节点并关联实体
for claim in claims:
    graph.add_node(f"claim_{claim_id}", node_type=NodeType.CLAIM, ...)
    # 关联实体
    for entity_id in claim.entities:
        graph.add_edge(claim_node, entity_node, edge_type=EdgeType.MENTIONS)

# 4. 添加假设节点并关联主张
for hypothesis in hypotheses:
    graph.add_node(f"hyp_{hyp_id}", node_type=NodeType.HYPOTHESIS, ...)
    # 关联支持的主张
    for claim_id in hypothesis.supporting_claims:
        graph.add_edge(claim_node, hyp_node, edge_type=EdgeType.SUPPORTS)
```

#### 6️⃣ 推理层 (`reasoning/`) 🧪

**功能**：从相关 claims 推断新假设

```python
from scidoc_reasoner.reasoning import HypothesisInferencer

inferencer = HypothesisInferencer()
inferred_hypotheses = inferencer.infer_hypotheses(
    graph, 
    min_supporting_claims=2,
    max_hypotheses=10
)

# 推断逻辑：
# 1. 找到共享实体的 claim 集群
# 2. 使用 LLM 推断这些 claims 背后的共同假设
# 3. 添加推断的假设到图中
```

**深度解析**：

**推断流程**：
1. **Claim 聚类**：
   - 通过共享实体聚类 claims
   - 通过 `EXTENDS` 边找到相关 claims
   - 最小支持数：至少 2 个相关 claims

2. **LLM 推断**：
   ```
   Given the following related scientific claims from different papers,
   infer the underlying shared hypothesis that these claims collectively support or test.
   
   Claims:
   Claim 1: "Method A outperforms Method B on dataset X"
   Claim 2: "Method A achieves 95% accuracy on long sequences"
   Claim 3: "Method B struggles with sequences longer than 512 tokens"
   
   A hypothesis should be:
   - A testable prediction or assumption
   - More general than the individual claims
   - Something that could explain or unify these claims
   ```

3. **结果验证**：
   - 置信度评分
   - 推理过程说明
   - 关联到支持 claims

**推断示例**：
```python
# 输入：相关 claims
claims = [
    "Sparse attention reduces memory usage by 50%",
    "Sparse attention maintains 98% accuracy",
    "Sparse attention scales to 10K tokens"
]

# 推断的假设
hypothesis = {
    "text": "Sparse attention mechanisms can efficiently scale to long sequences while maintaining model accuracy",
    "confidence": 0.82,
    "supporting_claims": ["claim_1", "claim_2", "claim_3"],
    "source": "inferred"
}
```

#### 7️⃣ 查询层 (`query/`) 🔍

**功能**：在推理图上执行复杂查询

```python
from scidoc_reasoner.query import QueryEngine

engine = QueryEngine(graph)

# 查询 1: 假设的支持/反驳情况
result = engine.query_hypothesis_support(
    hypothesis_text="Sparse attention improves efficiency"
)
# 返回: supporting claims, contradicting claims, documents

# 查询 2: 实体的研究演化路径
result = engine.query_entity_evolution(entity_name="Transformer")
# 返回: evolution_path, related_claims, related_hypotheses

# 查询 3: 未充分验证的假设
result = engine.query_unvalidated_hypotheses(
    min_support=2,
    max_contradictions=1
)
# 返回: 支持数 < 2 或反驳数 > 1 的假设

# 查询 4: Claim 之间的关系
result = engine.query_claim_relationships(claim_id="claim_123")
# 返回: 支持、反驳、延伸该 claim 的其他 claims
```

**深度解析**：

**查询 1: Hypothesis Support**
```python
def query_hypothesis_support(self, hypothesis_id, hypothesis_text):
    # 1. 找到假设节点
    hyp_node = self._find_hypothesis_node(hypothesis_id, hypothesis_text)
    
    # 2. 遍历前驱节点（支持的主张）
    for predecessor in graph.predecessors(hyp_node):
        if edge_type == EdgeType.SUPPORTS:
            supporting_claims.append(predecessor)
    
    # 3. 遍历后继节点（反驳的主张）
    for successor in graph.successors(hyp_node):
        if edge_type == EdgeType.CONTRADICTS:
            contradicting_claims.append(successor)
    
    # 4. 聚合文档信息
    return {
        "hypothesis": {...},
        "supporting": [...],
        "contradicting": [...],
        "documents": [...]
    }
```

**查询 2: Entity Evolution**
- 找到所有提及该实体的 claims
- 按文档/时间排序，形成演化路径
- 关联相关的假设

**查询 3: Unvalidated Hypotheses**
- 统计每个假设的支持数（`SUPPORTS` 边）
- 统计每个假设的反驳数（`CONTRADICTS` 边）
- 筛选出支持不足或反驳过多的假设

---

## 🚀 快速开始

### 📦 安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/scidoc-reasoner.git
cd scidoc-reasoner

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载 spaCy 模型
python -m spacy download en_core_web_sm
```

### ⚙️ 配置

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 💻 基本使用

#### 方式 1: Python API

```python
from scidoc_reasoner.ingest import PDFParser
from scidoc_reasoner.preprocess import SentenceSplitter
from scidoc_reasoner.extraction import (
    EntityExtractor, ClaimExtractor, HypothesisDetector
)
from scidoc_reasoner.linking import EntityLinker
from scidoc_reasoner.graph import GraphBuilder
from scidoc_reasoner.reasoning import HypothesisInferencer
from scidoc_reasoner.query import QueryEngine
from scidoc_reasoner.utils.storage import StructuredStorage

# 1. 解析文档
parser = PDFParser()
doc = parser.parse("paper1.pdf")
storage = StructuredStorage()
storage.save_document(doc.doc_id, doc.model_dump())

# 2. 预处理
splitter = SentenceSplitter()
sections = [{"section": s.section, "raw_text": s.raw_text, "sentences": s.sentences} 
            for s in doc.sections]
sentences = splitter.split_document(doc.doc_id, sections)

# 3. 抽取
entity_extractor = EntityExtractor()
entities = entity_extractor.extract_entities([s.model_dump() for s in sentences])

claim_extractor = ClaimExtractor()
claims = claim_extractor.extract_claims(
    [s.model_dump() for s in sentences],
    [e.model_dump() for e in entities]
)

hypothesis_detector = HypothesisDetector()
hypotheses = hypothesis_detector.detect_hypotheses(
    [s.model_dump() for s in sentences],
    [c.model_dump() for c in claims]
)

# 4. 链接实体
linker = EntityLinker()
entity_links = linker.link_entities([e.model_dump() for e in entities])

# 5. 构建图
builder = GraphBuilder()
graph = builder.build_from_documents(
    documents=[doc.model_dump()],
    entities=[e.model_dump() for e in entities],
    claims=[c.model_dump() for c in claims],
    hypotheses=[h.model_dump() for h in hypotheses],
    entity_links=entity_links
)

# 6. 推断假设
inferencer = HypothesisInferencer()
inferred = inferencer.infer_hypotheses(graph)
graph = inferencer.add_inferred_hypotheses_to_graph(graph, inferred)

# 7. 查询
engine = QueryEngine(graph)
results = engine.query_hypothesis_support(
    hypothesis_text="Your hypothesis here"
)
print(results)
```

#### 方式 2: REST API

```bash
# 1. 启动服务
uvicorn scidoc_reasoner.api.app:app --reload

# 2. 上传文档
curl -X POST "http://localhost:8000/upload/pdf" \
  -F "file=@paper1.pdf"

# 3. 处理文档
curl -X POST "http://localhost:8000/process/{doc_id}"

# 4. 构建图（多文档）
curl -X POST "http://localhost:8000/build_graph" \
  -H "Content-Type: application/json" \
  -d '{"doc_ids": ["doc_abc123", "doc_def456"]}'

# 5. 查询
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_type": "hypothesis_support",
    "parameters": {
      "hypothesis_text": "Sparse attention improves efficiency"
    }
  }'
```

---

## 🎯 核心功能

### 1. 📄 多格式文档解析

- ✅ **PDF**: 支持学术论文 PDF（提取文本、元数据、章节）
- ✅ **HTML**: 支持 arXiv、博客、网页（BeautifulSoup 解析）
- ✅ **Markdown**: 支持 Markdown 文档（支持 YAML frontmatter）

**特性**：
- 自动章节识别
- 元数据提取（标题、作者、日期）
- 唯一文档 ID 生成

### 2. 🔬 科学语义单元提取

- **句子切分**：处理科学符号、引用、缩写
- **语义分类**：识别断言、比较、因果关系
- **上下文保留**：每个单元包含章节、位置信息

### 3. 🧠 LLM 驱动的信息抽取

- **实体抽取**：模型、方法、数据集、指标、生物/化学实体
- **主张抽取**：比较性、因果性、结论性主张
- **假设检测**：显式假设识别（"we hypothesize that..."）

**优势**：
- 批量处理优化
- 置信度评分
- 结构化 JSON 输出

### 4. 🔗 跨文档实体链接

- **字符串匹配**：精确匹配、模糊匹配、缩写识别
- **语义相似度**：基于 sentence-transformers 的 embedding
- **类型约束**：只链接相同类型的实体

### 5. 🕸️ 多文档语义推理图

**节点类型**：
- `Document`: 文档
- `Entity`: 实体
- `Claim`: 主张
- `Hypothesis`: 假设

**边类型**：
- `supports`: 支持关系
- `contradicts`: 反驳关系
- `extends`: 延伸关系
- `based_on`: 基于关系
- `mentions`: 提及关系
- `contains`: 包含关系
- `links_to`: 链接关系

### 6. 🧪 假设推断引擎

- **Claim 聚类**：通过共享实体或关系边聚类
- **LLM 推断**：从相关 claims 推断共同假设
- **置信度评估**：为推断的假设评分

### 7. 🔍 强大的查询能力

**4 种查询类型**：
1. **Hypothesis Support**: 查询假设的支持/反驳情况
2. **Entity Evolution**: 查询实体的研究演化路径
3. **Unvalidated Hypotheses**: 发现未充分验证的假设
4. **Claim Relationships**: 查询 claim 之间的关系网络

---

## 📊 数据流示例

### 完整流程

```python
# 输入：3 篇相关论文
papers = ["paper1.pdf", "paper2.pdf", "paper3.pdf"]

# 步骤 1: 解析
docs = [PDFParser().parse(p) for p in papers]

# 步骤 2: 预处理
all_sentences = []
for doc in docs:
    sentences = SentenceSplitter().split_document(doc.doc_id, doc.sections)
    all_sentences.extend(sentences)

# 步骤 3: 抽取
all_entities = EntityExtractor().extract_entities(all_sentences)
all_claims = ClaimExtractor().extract_claims(all_sentences, all_entities)
all_hypotheses = HypothesisDetector().detect_hypotheses(all_sentences, all_claims)

# 步骤 4: 链接
entity_links = EntityLinker().link_entities(all_entities)
# 结果: {"Transformer": ["ent_1", "ent_5"], "BERT": ["ent_2", "ent_8"]}

# 步骤 5: 构建图
graph = GraphBuilder().build_from_documents(
    documents=docs,
    entities=all_entities,
    claims=all_claims,
    hypotheses=all_hypotheses,
    entity_links=entity_links
)
# 图结构: 50 个节点, 120 条边

# 步骤 6: 推断
inferred = HypothesisInferencer().infer_hypotheses(graph)
# 推断出 3 个新假设

# 步骤 7: 查询
engine = QueryEngine(graph)
results = engine.query_entity_evolution(entity_name="Transformer")
# 返回: 10 个相关 claims, 2 个相关假设, 演化路径
```

---

## 🛠️ API 接口

### REST API 端点

#### 1. 文档上传

```http
POST /upload/pdf
POST /upload/html
POST /upload/markdown
```

**请求**：
```bash
curl -X POST "http://localhost:8000/upload/pdf" \
  -F "file=@paper.pdf"
```

**响应**：
```json
{
  "doc_id": "doc_abc123",
  "title": "Attention Is All You Need",
  "status": "parsed"
}
```

#### 2. 文档处理

```http
POST /process/{doc_id}
```

**响应**：
```json
{
  "doc_id": "doc_abc123",
  "sentences": 450,
  "entities": 25,
  "claims": 18,
  "hypotheses": 3,
  "status": "processed"
}
```

#### 3. 构建图

```http
POST /build_graph
```

**请求**：
```json
{
  "doc_ids": ["doc_abc123", "doc_def456", "doc_ghi789"]
}
```

**响应**：
```json
{
  "status": "built",
  "num_nodes": 150,
  "num_edges": 320,
  "inferred_hypotheses": 5
}
```

#### 4. 查询

```http
POST /query
```

**请求**：
```json
{
  "query_type": "hypothesis_support",
  "parameters": {
    "hypothesis_text": "Sparse attention improves efficiency"
  }
}
```

**响应**：
```json
{
  "hypothesis": {
    "hypothesis_id": "hyp_123",
    "text": "Sparse attention improves efficiency",
    "confidence": 0.85
  },
  "supporting": [
    {
      "claim_id": "claim_1",
      "text": "Sparse attention reduces memory by 50%",
      "doc_id": "doc_abc123",
      "confidence": 0.9
    }
  ],
  "contradicting": [],
  "documents": [
    {
      "doc_id": "doc_abc123",
      "title": "Paper 1",
      "supports": true,
      "contradicts": false
    }
  ]
}
```

#### 5. 图统计

```http
GET /graph/stats
```

**响应**：
```json
{
  "num_nodes": 150,
  "num_edges": 320,
  "node_types": {
    "document": 3,
    "entity": 45,
    "claim": 72,
    "hypothesis": 30
  },
  "edge_types": {
    "supports": 50,
    "mentions": 120,
    "links_to": 30,
    "extends": 20,
    "contradicts": 5,
    "contains": 95
  }
}
```

---

## 📁 项目结构

```
scidoc_reasoner/
├── README.md                 # 项目文档（本文件）
├── requirements.txt          # Python 依赖
├── example_usage.py          # 使用示例
├── PROJECT_STRUCTURE.md      # 项目结构说明
│
├── scidoc_reasoner/         # 主包
│   ├── __init__.py
│   │
│   ├── ingest/              # 文档解析层
│   │   ├── __init__.py
│   │   ├── pdf_parser.py    # PDF 解析器
│   │   ├── html_parser.py   # HTML 解析器
│   │   └── md_parser.py     # Markdown 解析器
│   │
│   ├── preprocess/          # 预处理层
│   │   ├── __init__.py
│   │   ├── sentence_splitter.py  # 句子切分
│   │   └── clause_extractor.py   # 语义单元提取
│   │
│   ├── extraction/          # 抽取层（LLM）
│   │   ├── __init__.py
│   │   ├── entity_extractor.py      # 实体抽取
│   │   ├── claim_extractor.py       # 主张抽取
│   │   └── hypothesis_detector.py   # 假设检测
│   │
│   ├── linking/             # 链接层
│   │   ├── __init__.py
│   │   └── entity_linker.py        # 跨文档实体链接
│   │
│   ├── graph/               # 图构建层
│   │   ├── __init__.py
│   │   ├── graph_schema.py         # 图模式定义
│   │   └── graph_builder.py        # 图构建器
│   │
│   ├── reasoning/           # 推理层
│   │   ├── __init__.py
│   │   └── hypothesis_inferencer.py # 假设推断引擎
│   │
│   ├── query/               # 查询层
│   │   ├── __init__.py
│   │   └── query_engine.py         # 查询引擎
│   │
│   ├── api/                 # API 层
│   │   ├── __init__.py
│   │   └── app.py                  # FastAPI 应用
│   │
│   └── utils/               # 工具层
│       ├── __init__.py
│       └── storage.py              # 结构化存储
│
└── data/                    # 数据目录（自动创建）
    ├── storage/             # 结构化存储
    │   ├── documents/       # 解析的文档
    │   ├── entities/        # 抽取的实体
    │   ├── claims/          # 抽取的主张
    │   └── graphs/          # 构建的图
    └── temp/                # 临时文件
```

---

## 🎓 使用场景

### 1. 文献综述生成 📚

**场景**：快速了解某个领域的研究现状

```python
# 输入：10 篇相关论文
papers = ["transformer1.pdf", "transformer2.pdf", ...]

# 处理
graph = build_reasoning_graph(papers)

# 查询：Transformer 的研究演化
evolution = engine.query_entity_evolution("Transformer")
# 返回：按时间顺序的主张、假设演化路径
```

### 2. 假设验证 🔬

**场景**：验证某个假设是否被充分支持

```python
# 查询假设支持情况
support = engine.query_hypothesis_support(
    hypothesis_text="Sparse attention improves long-context modeling"
)

if len(support["supporting"]) < 3:
    print("⚠️ 假设支持不足，需要更多证据")
elif len(support["contradicting"]) > 0:
    print("⚠️ 存在反驳证据，需要进一步验证")
else:
    print("✅ 假设得到充分支持")
```

### 3. 发现研究空白 🕳️

**场景**：发现未被充分验证的假设

```python
# 查询未充分验证的假设
unvalidated = engine.query_unvalidated_hypotheses(
    min_support=2,
    max_contradictions=0
)

print(f"发现 {len(unvalidated)} 个未充分验证的假设")
for hyp in unvalidated:
    print(f"- {hyp['text']}")
    print(f"  支持数: {hyp['supporting_count']}, 反驳数: {hyp['contradicting_count']}")
```

### 4. 知识演化追踪 📈

**场景**：追踪某个概念在不同论文中的演化

```python
# 查询实体演化
evolution = engine.query_entity_evolution("BERT")

# 输出演化路径
for claim in evolution["evolution_path"]:
    print(f"[{claim['doc_id']}] {claim['text']}")
    print(f"  类型: {claim['claim_type']}, 置信度: {claim['confidence']}")
```

---

## 🔧 配置与优化

### 环境变量

```bash
# .env 文件
OPENAI_API_KEY=sk-...                    # OpenAI API Key（必需）
OPENAI_MODEL=gpt-4o-mini                 # 使用的模型（可选，默认 gpt-4o-mini）
EMBEDDING_MODEL=all-MiniLM-L6-v2         # Embedding 模型（可选）
ENTITY_LINKING_THRESHOLD=0.75            # 实体链接阈值（可选）
```

### 性能优化

1. **批量处理**：自动将句子/实体分批处理，避免 token 限制
2. **缓存**：结构化存储支持缓存，避免重复处理
3. **并行处理**：可以并行处理多个文档（需要手动实现）

### 扩展性

- **自定义实体类型**：修改 `EntityExtractor` 的 prompt
- **自定义边类型**：在 `graph_schema.py` 中添加新的 `EdgeType`
- **自定义查询**：在 `QueryEngine` 中添加新的查询方法

---

## 🧪 测试

```bash
# 运行示例
python example_usage.py

# 测试 API
curl http://localhost:8000/
```

---

## 📝 开发计划

### ✅ MVP 已完成

- [x] 文档解析（PDF, HTML, Markdown）
- [x] 句子切分与语义单元提取
- [x] 实体、主张、假设抽取
- [x] 跨文档实体链接
- [x] 多文档语义推理图构建
- [x] 假设推断引擎
- [x] 4 种查询类型
- [x] REST API 接口

### 🚧 后续扩展

- [ ] **时间演化分析**：追踪假设随时间的变化
- [ ] **置信度衰减/强化**：根据新证据更新置信度
- [ ] **引用加权推理**：考虑引用关系的重要性
- [ ] **审稿人式矛盾检测**：自动发现论文间的矛盾
- [ ] **可视化界面**：图结构可视化工具
- [ ] **批量处理优化**：支持大规模文档集（100+ 论文）

---

## 🤝 贡献

欢迎贡献！请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)（如果存在）。

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- [OpenAI](https://openai.com/) - 提供 LLM API
- [NetworkX](https://networkx.org/) - 图数据结构
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [sentence-transformers](https://www.sbert.net/) - Embedding 模型

---

## 👤 作者 (Author)

**Haoze Zheng**

*   🎓 **School**: Xinjiang University (XJU)
*   📧 **Email**: zhenghaoze@stu.xju.edu.cn
*   🐱 **GitHub**: [mire403](https://github.com/mire403)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

<sub>Made by Haoze Zheng. 2026 VoiceDataExplorer.</sub>

</div>





