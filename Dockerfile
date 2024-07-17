FROM python:3.11
WORKDIR /bot
COPY requirements.txt /bot/
RUN pip install -r requirements.txt
RUN sh render-build.sh
RUN export PATH="${PATH}:/opt/render/project/.render/chrome/opt/google/chrome"
COPY . /bot
CMD python main.py
