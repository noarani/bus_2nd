FROM python:3.11
WORKDIR /bot
COPY requirements.txt /bot/
COPY render-build.sh /bot/

RUN pip install -r requirements.txt
RUN sh render-build.sh
RUN export PATH="${PATH}:/opt/render/project/.render/chrome/opt/google/chrome"
RUN apt -f install
COPY . /bot
CMD python main.py
