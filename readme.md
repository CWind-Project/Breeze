# Breeze

Breeze 可以更好的帮助你编译一个 CWind 项目

---

## I. Prepare

### 1.1 Requirements

Breeze 除了依赖[`pyproject.toml`](https://github.com/CWind-Project/Breeze/blob/dev/pyproject.toml)中所列出的内容外, 

现阶段还依赖[`cwindf`](https://github.com/StarWindv/CWind-Lang/tree/main/mvp/frontend)

**Other requirements:**

Breeze 所依赖的第三方库如下:

 - [rich](https://github.com/Textualize/rich): 以 MIT 开源
 - [dulwich](https://github.com/jelmer/dulwich): 以 Apache-2.0 开源

### 1.2 Install

首先你需要激活你的`cwindf`所在的虚拟环境,

如果你还没有安装它, 那么 breeze 将无法使用

之后即可像安装一个普通软件包一样, 直接执行下列命令

```shell
pip install ./
```

---

## II. Usage


### 2.1 Sub Command

现阶段 Breeze 有以下用法:

| Command                       | Description                                          |
|-------------------------------|------------------------------------------------------|
| breeze                        | 展示完整帮助, 无参数                                 |
| breeze help [`command`]       | 查看某命令的说明                                     |
| breeze new [`path`]           | 在给定路径新建一个合法项目                           |
| breeze check Optional[`path`] | 检查给定路径的项目是否合法, 不提供路径则使用工作目录 |
| breeze build Optional[`path`] | 尝试编译指定路径的项目, 不提供路径则使用工作目录     |
| breeze version                | 输出当前使用的 breeze 版本                           |

### 2.2 Options

#### 2.2.1 new

| Option | Description                    |
|--------|--------------------------------|
| --lib  | 生成一个编译到链接库的白板项目 |

#### 2.2.2 build / check

| Option                      | 适用范围 | Description              |
|-----------------------------|----------|--------------------------|
| --build-args "arg1 arg2"    | 仅 build | 向`cwindc`传递自定义参数 |
| --frontend-args "arg1 arg2" | both     | 向`cwindf`传递自定义参数 |

#### 2.2.3 help

help 可以接收全部的其它顶级子命令

此处仅标注两个未被写出的特殊用法

| Option   | Description              |
|----------|--------------------------|
| frontend | 调用`cwindf`输出前端帮助 |
| backend  | 调用`cwindc`输出后端帮助 |

---

## III. Contributing

找到了漏洞? 我们很高兴接收它们!

请提交相关信息至 GitHub [issue tracker][issues].

[issues]: https://github.com/cwind-project/breeze/issues

---

## License

Breeze 所依赖的三方库(指非`CWind-Project`或`StarWindv`的库)许可均已在上文提到, 此处不再赘述

Breeze 自身以`BSD-3-Clause`开源
