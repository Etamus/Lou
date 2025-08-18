# LouEditor.py
import json
import re
from pathlib import Path
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QWidget, QFormLayout, QLineEdit, QTextEdit,
    QLabel, QMessageBox, QListWidget, QStackedWidget, QSplitter, QListWidgetItem,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal, QByteArray, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

class PersonalityEditorWindow(QDialog):
    """Uma janela de diálogo para editar o arquivo de personalidade da Lou."""
    personality_saved = Signal()

    def __init__(self, personality_file_path, parent=None):
        super().__init__(parent)
        self.personality_file = Path(personality_file_path)
        self.data = {}
        self.input_widgets = {}

        self.TRANSLATIONS = {
            # ... (dicionário de traduções completo, como na versão anterior)
            "IdentificacaoGeral": "Identificação Geral", "AparenciaFisicaEstilo": "Aparência e Estilo",
            "TraitsPersonalidade": "Traços de Personalidade", "PsicologiaProfunda": "Psicologia Profunda",
            "InteligenciaProcessamentoCognitivo": "Inteligência e Cognição", "ComportamentoSocial": "Comportamento Social",
            "Comunicacao": "Comunicação", "ValoresEMoral": "Valores e Moral", "EstiloDeVida": "Estilo de Vida",
            "RelacoesEAfetos": "Relações e Afetos", "EmocoesEReacoes": "Emoções e Reações",
            "HistoricoEExperiencias": "Histórico e Experiências", "ObjetivosEProjecaoFutura": "Objetivos e Futuro",
            "FamiliaELaçosFamiliares": "Família e Laços", "NomeCompleto": "Nome Completo", "Apelidos": "Apelidos", 
            "IdadeReal": "Idade", "Genero": "Gênero", "PronomePreferido": "Pronome Preferido", 
            "DataNascimento": "Data de Nascimento", "LocalNascimento": "Local de Nascimento",
            "LocalResidenciaAtual": "Residência Atual", "Nacionalidade": "Nacionalidade", "Ocupacao": "Ocupação",
            "ClasseSocialPercebida": "Classe Social Percebida", "TipoCorpo": "Tipo de Corpo", "TomPele": "Tom de Pele",
            "CorTipoCabelo": "Cor e Tipo de Cabelo", "CorOlhos": "Cor dos Olhos", "MarcasCicatrizes": "Marcas ou Cicatrizes",
            "PosturaAndar": "Postura e Andar", "EstiloVestimenta": "Estilo de Vestimenta", "HigienePessoal": "Higiene Pessoal",
            "ExpressoesFaciaisComuns": "Expressões Faciais Comuns", "GestosCaracteristicos": "Gestos Característicos",
            "QualidadesPrincipais": "Qualidades Principais", "DefeitosPrincipais": "Defeitos Principais",
            "NivelExtroversaoIntroversao": "Nível de Extroversão/Introversão", "NivelOtimismoPessimismo": "Nível de Otimismo/Pessimismo",
            "NivelEmpatia": "Nível de Empatia", "ToleranciaEstresse": "Tolerância ao Estresse", "ControleEmocional": "Controle Emocional",
            "Autoconfianca": "Autoconfiança", "FlexibilidadeMental": "Flexibilidade Mental", "NivelImpulsividade": "Nível de Impulsividade",
            "NecessidadeAprovacao": "Necessidade de Aprovação", "MedosPrincipais": "Medos Principais", "Insegurancas": "Inseguranças",
            "TraumasPassados": "Traumas Passados", "CrençasCentraisSobreSiMesmo": "Crenças Sobre Si Mesmo",
            "CrençasSobreOMundo": "Crenças Sobre o Mundo", "CrençasSobreOutrasPessoas": "Crenças Sobre Outras Pessoas",
            "DesejosMaisProfundos": "Desejos Mais Profundos", "ObjetivosDeVida": "Objetivos de Vida", "LimitesPessoais": "Limites Pessoais",
            "AssuntosQueEvitam": "Assuntos que Evita", "TranstornosCondicoesMentais": "Transtornos/Condições Mentais",
            "GatilhosEmocionais": "Gatilhos Emocionais", "MecanismosDeDefesa": "Mecanismos de Defesa", "EstrategiasDeEnfrentamento": "Estratégias de Enfrentamento",
            "PadroesDePensamentoRecorrentes": "Padrões de Pensamento Recorrentes", "TipoInteligenciaPredominante": "Tipo de Inteligência Predominante",
            "FormaDeAprenderMelhor": "Melhor Forma de Aprender", "FormaDeSeExpressarMelhor": "Melhor Forma de se Expressar",
            "VelocidadeRaciocinio": "Velocidade de Raciocínio", "AtencaoFoco": "Atenção e Foco", "CapacidadeMemorizacao": "Capacidade de Memorização",
            "HabilidadesAnaliticas": "Habilidades Analíticas", "NivelCuriosidade": "Nível de Curiosidade", "NivelSociabilidade": "Nível de Sociabilidade",
            "FormaSeApresentarEstranhos": "Como se Apresenta a Estranhos", "ReacaoCriticas": "Reação a Críticas",
            "ReacaoElogios": "Reação a Elogios", "FormaLidarConflitos": "Como Lida com Conflitos", "PreferenciaTrabalhoGrupoOuSozinho": "Preferência de Trabalho (Grupo/Sozinho)",
            "PapelComunEmGrupos": "Papel Comum em Grupos", "CapacidadeNegociar": "Capacidade de Negociar", "LinguagemCorporalPredominante": "Linguagem Corporal Predominante",
            "TomDeVoz": "Tom de Voz", "VelocidadeAoFalar": "Velocidade ao Falar", "Expressividade": "Expressividade", "Vocabulario": "Vocabulário",
            "UsoDeGirias": "Uso de Gírias", "FormaDeContarHistorias": "Forma de Contar Histórias", "SensoDeHumor": "Senso de Humor",
            "NivelSinceridadeDiplomacia": "Nível de Sinceridade/Diplomacia", "PrincipiosInegociaveis": "Princípios Inegociáveis",
            "CausaOuIdeal": "Causa ou Ideal", "NivelReligiosidadeEspiritualidade": "Religiosidade/Espiritualidade",
            "PosicionamentoPolitico": "Posicionamento Político", "VisaoSobreJustica": "Visão Sobre Justiça", "VisaoSobreCertoErrado": "Visão Sobre Certo e Errado",
            "RegrasProprias": "Regras Próprias", "RotinaDiaria": "Rotina Diária", "HorarioMaiorEnergia": "Horário de Maior Energia",
            "HobbiesPassatempos": "Hobbies e Passatempos", "InteressesCulinarios": "Interesses Culinários", "PreferenciasMusicais": "Preferências Musicais",
            "PreferenciasDeLeitura": "Preferências de Leitura", "PreferenciasDeLazer": "Preferências de Lazer", "ViagensExperienciasMarcantes": "Viagens e Experiências Marcantes",
            "NivelAtividadeFisica": "Nível de Atividade Física", "Alimentacao": "Alimentação", "RelacaoComTecnologia": "Relação com Tecnologia",
            "TipoVinculoMaisValoriza": "Vínculo que Mais Valoriza", "FormaDemonstrarAfeto": "Forma de Demonstrar Afeto", "ExpectativasRelacionamentos": "Expectativas em Relacionamentos",
            "FormaLidarTerminoAfastamento": "Como Lida com Términos", "NivelCiumes": "Nível de Ciúmes", "ConfiancaEmPessoas": "Confiança em Pessoas",
            "HistoricoAmizadesAmoresImportantes": "Histórico de Amizades/Amores", "PresencaFigMentorasInspiradoras": "Presença de Figuras Inspiradoras",
            "EmocaoMaisFrequente": "Emoção Mais Frequente", "ReacaoSobPressao": "Reação Sob Pressão", "ReacaoAoFracasso": "Reação ao Fracasso",
            "ReacaoAoSucesso": "Reação ao Sucesso", "TendenciaGuardarExpressarEmocoes": "Tendência de Guardar/Expressar Emoções",
            "SituacoesGeramAnsiedade": "Situações que Geram Ansiedade", "SituacoesGeramCalma": "Situações que Geram Calma", "FormasDeSeAcalmar": "Formas de se Acalmar",
            "EventosMarcantesInfancia": "Eventos Marcantes (Infância)", "EventosMarcantesAdolescencia": "Eventos Marcantes (Adolescência)",
            "EventosMarcantesVidaAdulta": "Eventos Marcantes (Vida Adulta)", "PrincipaisConquistas": "Principais Conquistas", "PrincipaisPerdas": "Principais Perdas",
            "MomentosMudaramFormaDePensar": "Momentos que Mudaram a Forma de Pensar", "MetasCurtoPrazo": "Metas de Curto Prazo",
            "MetasLongoPrazo": "Metas de Longo Prazo", "MedosFuturo": "Medos sobre o Futuro", "PlanosParaSuperar": "Planos para Superar Medos",
            "ComoDesejaSerLembrado": "Como Deseja Ser Lembrado", "NomeCompletoPai": "Nome Completo do Pai", "ApelidosPai": "Apelidos do Pai",
            "ComposicaoFamiliarAtual": "Composição Familiar Atual", "ComQuemMora": "Com Quem Mora", "RelacaoComPai": "Relação com o Pai",
            "RelacaoComMae": "Relação com a Mãe", "RelacaoComIrmaos": "Relação com Irmãos", "EventosFamiliaresMarcantesPositivos": "Eventos Familiares Positivos",
            "EventosFamiliaresMarcantesNegativos": "Eventos Familiares Negativos", "HerancaCulturalTradicoesFamiliares": "Herança Cultural e Tradições",
            "CostumesFamiliaresMantidos": "Costumes Familiares Mantidos", "HistoriasNarrativasFamiliaresImportantes": "Histórias Familiares Importantes",
            "ExpectativasFamiliares": "Expectativas Familiares", "InfluenciasFamiliaresNasEscolhas": "Influências Familiares nas Escolhas",
            "PapelNaFamilia": "Papel na Família"
        }
        
        self.setWindowTitle("Editor de Personalidade")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog { background-color: #2f3136; color: #dcddde; }
            QLabel { font-size: 10pt; color: #b9bbbe; padding-right: 10px; }
            QLineEdit, QTextEdit { background-color: #202225; color: #dcddde; border: 1px solid #202225; border-radius: 3px; padding: 8px; font-size: 10pt; }
            QPushButton { background-color: #5865f2; color: #ffffff; border: none; padding: 10px 20px; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #4f5acb; }
            QPushButton#cancelButton, QPushButton#backupButton { background-color: #4f545c; }
            QPushButton#cancelButton:hover, QPushButton#backupButton:hover { background-color: #5d636b; }
            QScrollArea { border: none; background-color: #36393f; }
            QSplitter::handle { background-color: #202225; }
            QListWidget { background-color: #2f3136; border: none; font-size: 11pt; outline: 0; padding: 5px; }
            QListWidget::item { padding: 12px; margin: 2px 5px; border-radius: 4px; border-left: 3px solid transparent; }
            QListWidget::item:hover { background-color: #3a3d43; }
            QListWidget::item:selected { background-color: #40444b; color: white; font-weight: bold; border-left: 3px solid #ffffff; }
        """)

        self.main_layout = QVBoxLayout(self)
        self.content_splitter = QSplitter(Qt.Horizontal)
        self.category_list = QListWidget()
        self.panel_stack = QStackedWidget()
        self.content_splitter.addWidget(self.category_list); self.content_splitter.addWidget(self.panel_stack)
        self.content_splitter.setSizes([260, 540])
        self.main_layout.addWidget(self.content_splitter)
        self.load_data_and_build_ui()
        self.category_list.currentRowChanged.connect(self.panel_stack.setCurrentIndex)
        
        # --- BOTÕES DE AÇÃO ---
        self.button_layout = QHBoxLayout()
        # Novos botões de Backup/Carregar à esquerda
        load_backup_button = QPushButton("Carregar JSON"); load_backup_button.setObjectName("backupButton"); load_backup_button.clicked.connect(self._load_backup)
        save_backup_button = QPushButton("Criar Backup"); save_backup_button.setObjectName("backupButton"); save_backup_button.clicked.connect(self._save_backup)
        self.button_layout.addWidget(load_backup_button)
        self.button_layout.addWidget(save_backup_button)
        self.button_layout.addStretch()
        # Botões de Salvar/Cancelar à direita
        cancel_button = QPushButton("Cancelar"); cancel_button.setObjectName("cancelButton")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Salvar"); save_button.clicked.connect(self.save_changes)
        self.button_layout.addWidget(cancel_button); self.button_layout.addWidget(save_button)
        self.main_layout.addLayout(self.button_layout)

    def _get_display_name(self, key):
        return self.TRANSLATIONS.get(key, re.sub(r'(?<!^)(?=[A-Z])', ' ', key).title())

    def _clear_ui(self):
        """Limpa a UI para recarregar novos dados."""
        self.panel_stack.blockSignals(True)
        self.category_list.blockSignals(True)
        
        self.category_list.clear()
        while self.panel_stack.count() > 0:
            widget = self.panel_stack.widget(0)
            self.panel_stack.removeWidget(widget)
            widget.deleteLater()
        self.input_widgets.clear()
        
        self.panel_stack.blockSignals(False)
        self.category_list.blockSignals(False)

    def load_data_and_build_ui(self):
        if not self.data: # Carrega apenas se não houver dados
            try:
                with open(self.personality_file, "r", encoding="utf-8") as f: self.data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                QMessageBox.critical(self, "Erro", "Não foi possível carregar o arquivo de personalidade."); return
        
        self._clear_ui()
        personality_def = self.data.get("personality_definition", {})
        for category, details in personality_def.items():
            scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            form_widget = QWidget(); form_layout = QFormLayout(form_widget)
            form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
            form_layout.setLabelAlignment(Qt.AlignTop | Qt.AlignLeft)
            form_layout.setSpacing(15); form_layout.setContentsMargins(15, 15, 15, 15)
            self._populate_form(form_layout, details, category)
            scroll_area.setWidget(form_widget)
            self.panel_stack.addWidget(scroll_area)
            category_name = self._get_display_name(category)
            item = QListWidgetItem(category_name)
            self.category_list.addItem(item)
        if self.category_list.count() > 0: self.category_list.setCurrentRow(0)

    def _populate_form(self, layout, data_dict, path):
        for key, value in data_dict.items():
            label_text = self._get_display_name(key)
            current_path = f"{path}.{key}"
            
            # Lógica especial restaurada para o campo de Data de Nascimento
            if key == "DataNascimento":
                try:
                    dt_object = datetime.strptime(str(value), '%Y-%m-%d')
                    display_text = dt_object.strftime('%d/%m/%Y')
                    editor = QLineEdit(display_text)
                except ValueError:
                    editor = QLineEdit(str(value))
            
            # Lógica para os outros campos (continua a mesma)
            elif isinstance(value, list):
                editor = QTextEdit(", ".join(map(str, value)))
                editor.setMinimumHeight(60)
            elif isinstance(value, str) and (len(value) > 80 or "\n" in value):
                editor = QTextEdit(value); editor.setMinimumHeight(80)
            else:
                editor = QLineEdit(str(value))
            
            layout.addRow(label_text, editor)
            self.input_widgets[current_path] = editor

    def _save_backup(self):
        """Abre um diálogo para salvar a personalidade atual em um arquivo de backup."""
        # Sugere um nome de arquivo com a data atual
        suggested_name = f"personality_backup_{datetime.now().strftime('%Y%m%d')}.json"
        file_path, _ = QFileDialog.getSaveFileName(self, "", suggested_name, "JSON Files (*.json)")
        
        if file_path:
            try:
                # Salva os dados ATUALMENTE CARREGADOS no editor
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Sucesso", "Backup criado com sucesso.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o backup:\n{e}")

    def _load_backup(self):
        """Abre um diálogo para carregar uma personalidade de um arquivo de backup."""
        file_path, _ = QFileDialog.getOpenFileName(self, "", "", "JSON Files (*.json)")

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                # Validação básica para garantir que é um arquivo de personalidade
                if "personality_definition" not in backup_data or "technical_rules" not in backup_data:
                    raise ValueError("Este não parece ser um arquivo de personalidade válido.")
                
                # Carrega os novos dados e reconstrói a UI
                self.data = backup_data
                self.load_data_and_build_ui()
                QMessageBox.information(self, "Sucesso", "Carregado com sucesso.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível carregar o backup:\n{e}")

    def save_changes(self):
        for path, widget in self.input_widgets.items():
            keys = path.split('.'); sub_dict = self.data["personality_definition"]
            for key in keys[:-1]: sub_dict = sub_dict[key]
            final_key = keys[-1]
            
            # Lógica especial restaurada para salvar o campo de Data de Nascimento
            if final_key == "DataNascimento":
                display_text = widget.text()
                try:
                    dt_object = datetime.strptime(display_text, '%d/%m/%Y')
                    save_text = dt_object.strftime('%Y-%m-%d')
                    sub_dict[final_key] = save_text
                except ValueError:
                    sub_dict[final_key] = display_text
                continue # Pula para o próximo item do loop

            # Lógica para os outros campos (continua a mesma)
            original_value = sub_dict[final_key]
            if isinstance(widget, QTextEdit):
                if isinstance(original_value, list):
                    sub_dict[final_key] = [item.strip() for item in widget.toPlainText().split(',') if item.strip()]
                else:
                    sub_dict[final_key] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                text = widget.text()
                try:
                    if isinstance(original_value, int): sub_dict[final_key] = int(text)
                    elif isinstance(original_value, float): sub_dict[final_key] = float(text)
                    else: sub_dict[final_key] = text
                except (ValueError, TypeError):
                     sub_dict[final_key] = text
        try:
            with open(self.personality_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            self.personality_saved.emit(); self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo:\n{e}")