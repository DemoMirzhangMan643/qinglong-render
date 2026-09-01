FROM whyour/qinglong:debian

# 复制自定义启动脚本并清理 Windows 换行符
COPY entrypoint.sh /ql/entrypoint-render.sh
RUN sed -i 's/\r$//' /ql/entrypoint-render.sh \
    && chmod +x /ql/entrypoint-render.sh \
    && sed -i 's/\r$//' /ql/start.sh \
    && chmod +x /ql/start.sh

EXPOSE 5700

CMD ["/bin/bash", "/ql/entrypoint-render.sh"]
