# StockV2.1 迭代日志

## 2026-05-07 [US Stock & Multi-Source Support]
### 1. 美股支持 (US Stocks)
- **代码识别**: 自动识别 1-5 位纯字母代码为美股（如 AAPL, NVDA, TSLA）。
- **实时行情**: 适配新浪（gb_前缀）和腾讯（us前缀）美股行情接口。
- **搜索增强**: 预置热门美股中英文映射（如“苹果”->AAPL），支持模糊搜索。

### 2. 数据源扩展 (Data Sources)
- **AkShare 回退机制**: 当 yfinance 无法获取 A 股数据时，系统自动切换至 AkShare 抓取历史 K 线。
- **稳定性优化**: `get_stock_data` 增加 `period` 参数备选逻辑，解决特定日期范围下 Yahoo Finance 返回空数据的问题。

### 3. Git 版本管理
- **本地提交**: 已将所有变更提交至本地仓库。
- **远程同步**: 配置远程仓库 `https://github.com/qcieng/StockV2.2_Analysis.git`。
- **配置优化**: 更新 `.gitignore` 以排除临时测试文件及数据库。
