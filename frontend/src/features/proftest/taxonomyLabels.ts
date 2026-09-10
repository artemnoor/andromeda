const AREA_LABELS: Record<string, string> = {
  mathematics_statistics: "Математика и статистика",
  computer_science_data: "Компьютерные науки и данные",
  physics_astronomy: "Физика и астрономия",
  chemistry_materials: "Химия и материаловедение",
  biology_biotechnology: "Биология и биотехнологии",
  earth_environment: "Земля, экология и окружающая среда",
  engineering_technology: "Инженерия и технологии",
  architecture_construction: "Архитектура, строительство и урбанистика",
  agriculture_veterinary: "Сельское хозяйство и ветеринария",
  medicine_health: "Медицина и здоровье",
  psychology_cognitive: "Психология и когнитивные науки",
  society_social_sciences: "Общество и социальные науки",
  economics_finance: "Экономика и финансы",
  business_management: "Бизнес, управление и предпринимательство",
  law_policy_public_administration: "Право, политика и государственное управление",
  languages_linguistics_literature: "Языки, лингвистика и литература",
  history_philosophy_humanities: "История, философия и гуманитарные науки",
  art_design_media: "Искусство, дизайн, медиа и коммуникации",
  education_pedagogy: "Образование и педагогика",
  sport_tourism_hospitality: "Спорт, туризм и индустрия гостеприимства",
  safety_defense_transport: "Безопасность, оборона и транспортные системы",
  universal_interdisciplinary: "Универсальные и междисциплинарные дисциплины",
};

export function areaLabel(area: string): string {
  return AREA_LABELS[area] ?? area;
}
