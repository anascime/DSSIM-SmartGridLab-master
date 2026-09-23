# import logging
# # presumindo que a variável loglevel está atrelada ao valor da string obtida
# # pelo argumento de linha de comando; Converter para caixa alta permite ao usuário
# # declarar tanto --log=DEBUG quanto--log=debug
# loglevel = 'debug'
# nivel_numerico = getattr(logging, loglevel.upper(), None)
# if not isinstance(nivel_numerico , int):
#     raise ValueError('Nível de log invalido: %s' % loglevel)
# logging.basicConfig(level=nivel_numerico,
#                     filename='exemplo.log',
#                     encoding='utf-8',
#                     format='%(asctime)s - %(levelname)s:%(name)s:%(message)s')
# logger = logging.getLogger(__name__)

# logger.debug('Esta mensagem aparecerá no arquivo de log')
# logger.info('Esta também')
# logger.warning('E também essa')
# logger.error('Além de palavras com caracteres não-ASCII, como Øresund e Malmö')

# file_handler = logging.FileHandler('app.log', encoding='utf-8')
# file_handler.setLevel(logging.INFO)
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger = logging.getLogger('meu_logger')
# logger.addHandler(file_handler)

# logger.debug('Mensagem de depuração.')
# logger.info('Mensagem informativa.')
# logger.warning('Mensagem de aviso.')
# logger.error('Mensagem de erro.')
# logger.critical('Mensagem crítica.')
# # Configuração básica do logging
# # logging.basicConfig(filename='app.log',
# #                     encoding='utf-8',
# #                     level=logging.DEBUG,
# #                     format='%(asctime)s - %(levelname)s - %(message)s')


# # Registrando diferentes níveis de logs
# logging.debug('Mensagem de debug')
# logging.info('Mensagem de informação')
# logging.warning('Mensagem de aviso')
# logging.error('alo alo Mensagem de erro')
# logging.critical('Mensagem crítica')

# # Verifique o arquivo app.log para ver os logs registrados

import logging
import logging.config
import yaml
import os

def init_logging():
    path = 'logging.yaml'
    if os.path.exists(path):
        with open(path, 'r') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config['logging'])
    main()


def main():
    logger = logging.getLogger('__name__')
    logger.debug("done!")
    logger.warning("alô cuidado! fique atento!")


init_logging()