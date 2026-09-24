# Breeze

Breeze 可以更好的帮助你编译一个 CWind 项目

---

## Start

### Requirements

Breeze 除了依赖[`pyproject.toml`](https://github.com/CWind-Project/Breeze/blob/dev/pyproject.toml)中所列出的内容外, 

现阶段还依赖[`cwindf`](https://github.com/StarWindv/CWind-Lang/tree/main/mvp/frontend)

**Other requirements:**

Breeze 所依赖的第三方库如下:

 - [rich](https://github.com/Textualize/rich): 以 MIT 开源
 - [dulwich](https://github.com/jelmer/dulwich): 以 Apache-2.0 开源

### Install

首先你需要激活你的`cwindf`所在的虚拟环境,

如果你还没有安装它, 那么 breeze 将无法使用

之后即可像安装一个普通软件包一样, 直接执行下列命令

```shell
pip install ./
```

---

## Contributing

找到了漏洞? 我们很高兴接收它们!

请提交相关信息至 GitHub [issue tracker][issues].

[issues]: https://github.com/cwind-project/breeze/issues

---

## License

Breeze 所依赖的三方库(指非`CWind-Project`或`StarWindv`的库)许可均已在上文提到, 此处不再赘述

Breeze 自身以`BSD-3-Clause`开源
