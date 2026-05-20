class ErrorMessages:
    # Erros gerais
    GENERIC_ERROR = "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde."

    # Erros de validação de entrada
    INVALID_INPUT = "A entrada fornecida é inválida. Verifique e tente novamente."
    REQUIRED_FIELD_MISSING = "Campo obrigatório ausente: {}"

    # Erros de conexão
    CONNECTION_ERROR = "Erro de conexão. Verifique sua internet ou tente novamente mais tarde."
    TIMEOUT_ERROR = "Tempo limite excedido. Tente novamente mais tarde."

    # Erros de autenticação
    UNAUTHORIZED_ACCESS = "Acesso não autorizado. Verifique suas credenciais."
    FORBIDDEN_ACCESS = "Acesso proibido. Você não tem permissão para realizar esta operação."

    # Erros de banco de dados
    DB_CONNECTION_ERROR = "Erro ao conectar ao banco de dados. Verifique as configurações de conexão."
    DB_QUERY_ERROR = "Erro ao executar a consulta no banco de dados: {}"

    # Erros de arquivos
    FILE_NOT_FOUND = "Arquivo não encontrado: {}"
    FILE_READ_ERROR = "Erro ao ler o arquivo: {}"
    FILE_WRITE_ERROR = "Erro ao gravar no arquivo: {}"

    # Erros de conversão de dados
    TYPE_CONVERSION_ERROR = "Erro ao tentar converter os dados para o tipo esperado."

    # Erros de lógica de negócio
    BUSINESS_LOGIC_ERROR = "Erro na lógica de negócios: {}"

    # Erros específicos
    ITEM_NOT_FOUND = "Item não encontrado: {}"
    OPERATION_NOT_ALLOWED = "Operação não permitida: {}"
