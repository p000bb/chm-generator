# get_chip_data

> 获取芯片数据

## 📋 功能说明

通过芯片配置信息，从中文官网和英文官网爬取最新的芯片数据，并生成 **Overview模块** 的概览页面：

- **中文官网** → `Overview_cn`
- **英文官网** → `Overview_en`

> 💡 **提示**：如果不输入英文官网，则 `Overview_en` 使用中文官网的数据，后续`translate_main_modules`脚本会使用谷歌翻译成英文。