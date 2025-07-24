import React from 'react';
import { useAppSelector } from '../../hooks/reduxHook';
import css from './forecastAugust2025.module.css';

const ForecastAugust2025 = () => {

  const theme = useAppSelector(state => state.theme.theme);
  
  return (
    <div className={theme ? css.containerLight : css.containerDark}>
      
      <h1>Прогноз на серпень 2025</h1>

      <div>
        <h2>Індивідуальний прогноз на серпень 2025</h2>
        <p style={{ textAlign: 'center' }}>
          Дата народження: <strong>15 квітня 1988</strong> | Знак: <strong>Овен</strong>
        </p>

        <h2>Загальна тенденція місяця</h2>
        <p>
          Серпень буде для вас місяцем активних дій і важливих рішень. Ви відчуєте приплив енергії,
          що підштовхне до нових проектів або завершення старих. Особливо сприятливий період для
          ініціатив у кар’єрі та особистих стосунках.
        </p>

        <div className={theme ? css.weekBlockLight : css.weekBlockDark}>
          <h2>1–7 серпня</h2>
          <p>
            Період напружений, але продуктивний. Можливі конфлікти на роботі, якщо не проявите
            гнучкість. Варто більше часу приділяти собі та своїм потребам. У вихідні — сприятливі
            дні для родинних справ.
          </p>
        </div>

        <div className={theme ? css.weekBlockLight : css.weekBlockDark}>
          <h2>8–14 серпня</h2>
          <p>
            Ваші ідеї можуть знайти підтримку. Спілкування з новими людьми надихне на зміни.
            Ідеальний час для навчання або короткої подорожі.
          </p>
        </div>

        <div className={theme ? css.weekBlockLight : css.weekBlockDark}>
          <h2>15–21 серпня</h2>
          <p>
            Час для любові та романтики. Стосунки можуть перейти на новий рівень. Але важливо не
            ігнорувати внутрішні тривоги – прислухайтесь до інтуїції.
          </p>
        </div>

        <div className={theme ? css.weekBlockLight : css.weekBlockDark}>
          <h2>22–31 серпня</h2>
          <p>
            Завершення справ, наведення порядку. Варто проаналізувати досягнуте за місяць. Ймовірні
            несподівані грошові надходження або пропозиції.
          </p>
        </div>

        <h2>Порада місяця</h2>
        <p>
          Не бійтеся заявити про себе. Ваш голос має силу. Але пам’ятайте: гнучкість — не слабкість,
          а мудрість.
        </p>
      </div>
    </div>
  );
};

export { ForecastAugust2025 };