"""OpenCord services — business logic layer.

每个 service 接收 session（通过依赖注入）和 DTO，输出 DTO 或 ORM 对象。
service 是未来插件替换的边界：v0.3+ 插件可替换 service 实现。
"""
