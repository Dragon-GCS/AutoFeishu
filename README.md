# AutoFeishu

飞书官方接口的Python封装， 需要自行注册飞书应用

## 参数配置

本项目使用`pydantic_settings`读取参数，有多种方法用于设置参数。优先级顺序如下:

- 代码中设置

  ```python
  from feishu import config
  config.api_key = 'xxx'
  config.api_secret = 'xx'
  ```

- 环境变量(case-insensitive): 所有相关环境变量以`FEISHU_`开头，例如`FEISHU_API_KEY`, `FEISHU_API_SECRET`

- `.feishu.env`, `.env`文件(case-insensitive)
- `pyproject.toml`文件(case-sensitive)

  ```toml
  [tool.auto-feishu]
  api_key = "xxx"
  api_secret = "xxx"
  ...
  ```

### 配置内容

- `api_key`: 飞书应用的`App ID`
- `api_secret`: 飞书应用的`App Secret`
- `base_url`: 飞书API的base url，默认`https://open.feishu.cn/open-apis`
- `phone`, `email`, `open_id`: 用于`Contact`获取默认的用户信息

> TODO: 文档`https://mkdocstrings.github.io/usage/`

## 当前接口

- `Approval`: 创建、同意、拒绝审批，获取审批详情
- `Contact`: 根据手机号或邮箱获取open_id
- `Message`: 向指定联系人或群发送文本、文件、图片、卡片
- `SpreadSheet`: 读写多维表格
- `Group`: 群组管理

## 新增接口开发

继承`feishu.client.BaseClient`。

- `AuthClient`封装了`get`, `post`, `put`, `_request`等方法，可以自动鉴权发送HTTP请求。
- `AuthClient`包含一个使用默认`app_id`和`app_secret`的`default_client`, 可以在classmethod中使用
- `feishu.client.Cache`是一个自动区分当前app的描述器，可以用来缓存数据。样例参见`feishu.contact.Contact`
- 属性`api`用于保存各个api的别名和url: `{name: /api, ...}`
