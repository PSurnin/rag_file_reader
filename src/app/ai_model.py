from typing import Dict
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

import torch
import gc

from src.logger import log

# TODO: Настройка параметров генерации - длина ответа и стиль
# TODO: RAG + FAISS


class ModelManager:
    def __init__(self, model_name: str = "HuggingFaceTB/SmolLM3-3B"):
        self.model = None
        self.model_name = model_name
        self.tokenizer = None
        self.is_loaded = False
        self.device = "cuda"

    def load_model(self):
        """Загрузка модели с кэшированием"""
        if self.is_loaded:
            return

        try:
            log.info(f"Загрузка модели: {self.model_name}")

            # Конфигурация квантования
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )

            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir="/model_data/smolLM3",
                quantization_config=bnb_config,
                low_cpu_mem_usage=True,
                torch_dtype=torch.float16,
                use_safetensors=True,
            ).to("cuda")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir="/model_data/smolLM3",
                torch_dtype=torch.float16,
            )

            self.device = next(self.model.parameters()).device
            self.is_loaded = True

            log.info(f"Модель загружена на устройство: {self.device}")
            log.info(
                f"VRAM: {torch.cuda.memory_allocated() / 1024**3:.2f} GB"
            )

        except Exception as e:
            log.error(f"Ошибка загрузки модели: {e}")
            raise

    def _clear_cache(self):
        """Очистка GPU кэша после инференса"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()

    def _prepare_input(
        self,
        text: str,
        max_length: int = 2048,
    ) -> Dict[str, torch.Tensor]:
        """Подготовка входных данных с правильной токенизацией"""
        # Токенизация с учетом максимальной длины
        tokens = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=False,
        )
        return {k: v.to(self.device) for k, v in tokens.items()}

    def summarize(self, text: str, max_new_tokens: int = 150) -> str:
        """Генерация краткого содержания"""
        if not self.is_loaded:
            self.load_model()

        try:
            prompt = f"""
            <|system|>You are an assistant that creates concise
            and accurate document summaries.
            <|user|>Here is a document text.
            Create a brief summary (1-2 paragraphs)
            that captures the main topic and key ideas.
            Use plain text format only, no markdown or HTML tags:
            {text}
            Summary:<|assistant|>"""
            inputs = self._prepare_input(prompt)

            # Генерация с настроенным декодированием
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Извлечение только сгенерированной части
            generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            summary = self.tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True,
            )

            return summary.strip()

        finally:
            self._clear_cache()

    def unload_model(self):
        """Освобождение ресурсов"""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        self._clear_cache()
        self.is_loaded = False
        log.info("Модель выгружена")


model_manager = ModelManager()
