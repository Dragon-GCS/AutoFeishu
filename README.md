# AutoFeishu

飞书官方接口的Python封装， 需要自行注册飞书应用，将应用的`app_id`和`app_secret`填入到环境变量`FEISHU_APP_ID`和`FEISHU_APP_SECRET`中。

部分接口需要设置其他环境变量:

- `Contact`: 通过`FEISHU_PHONE`或`FEISHU_EMAIL`或`FEISHU_OPEN_ID`获取默认的用户信息，可以用于`Message`
