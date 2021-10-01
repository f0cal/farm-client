FROM python:3.7-slim
RUN pip install --upgrade pip setuptools wheel
ENV PYPI="-i http://localhost:3141/root/dev"
RUN pip install f0cal.farm.client $PYPI
COPY entrypoint.sh ./
CMD bash entrypoint.sh
