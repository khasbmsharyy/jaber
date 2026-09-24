const express = require('express');
const fs = require('fs');
const path = require('path');
const pdfParse = require('pdf-parse');

const app = express();
const PORT = process.env.PORT || 3000;
const ROOT = __dirname;
const PDF = path.join(ROOT, 'تمارين جبر خطي(2).pdf');
const OUT = path.join(ROOT, 'pdf_questions.json');

const TOPICS = [
  ['منظومة المعادلات الخطية', ['معادلات','منظومة','جاوس','الحذف']],
  ['المصفوفات والعمليات عليها', ['مصفوف','رتبة','صفوف','أعمدة','عمليات سطرية']],
  ['أنواع المصفوفات', ['قطرية','وحدية','مثلثية','منقولة']],
  ['كتابة عناصر المصفوفة', ['عناصر المصفوفة','بحسب الشروط','aij','aᵢⱼ']],
  ['المصفوفات الأولية', ['مصفوفة أولية','مصفوفات أولية']],
  ['المحددات وخواصها', ['محدد','det','قيمة المحدد','خواص المحدد']],
  ['العوامل المرافقة', ['عامل مرافق','العوامل المرافقة','القاصر','cofactor']],
  ['المتجهات والضرب العددي', ['متجه','ضرب قياسي','ضرب عددي','زاوية']],
  ['المركبات والضرب الاتجاهي', ['مركبة أفقية','مركبة عمودية','ضرب اتجاهي','cross']],
  ['المتجهات الواحدية والمتعامدة', ['متجه واحدي','متجهات واحدية','متعامدة','متعامد قياسياً']],
  ['المستقيمات والمستويات والمسافة', ['مستقيم','مستوى','المسافة','بعد نقطة']],
  ['فضاءات المتجهات والاستقلال الخطي', ['فضاء متجهات','فضاء المتجهات','استقلال','ارتباط']],
  ['التحويلات الخطية', ['تحويل خطي','تحويلات خطية']]
];

function normalize(value) {
  return value.replace(/\u0640/g, '').replace(/\s+/g, ' ').trim();
}
function digits(value) {
  return value.replace(/[٠-٩]/g, c => '٠١٢٣٤٥٦٧٨٩'.indexOf(c));
}
function topicFor(text, current = 'عام') {
  const lower = text.toLowerCase();
  for (const [name, words] of TOPICS) {
    if (words.some(word => lower.includes(word.toLowerCase()))) return name;
  }
  return current;
}
function splitQuestions(text) {
  const source = digits(text.replace(/\r/g, '\n'));
  const starts = [...source.matchAll(/(?:^|\n)\s*(?:سؤال\s*)?(\d+)\s*[\)\].،.\-:：]\s*/g)];
  if (starts.length) return starts.map((m, i) => normalize(source.slice(m.index + m[0].length, starts[i + 1]?.index ?? source.length))).filter(q => q.length >= 4);
  return normalize(source).split(/(?<=[؟?])\s+/).filter(q => q.includes('؟') || q.includes('?'));
}
async function extract() {
  if (!fs.existsSync(PDF)) throw new Error(`ملف PDF غير موجود: ${PDF}`);
  const data = await pdfParse(fs.readFileSync(PDF));
  const pages = data.text.split('\f');
  const questions = [];
  let current = 'عام';
  pages.forEach((raw, pageIndex) => {
    if (!raw.trim()) return;
    const page = normalize(raw);
    const detected = topicFor(page, current);
    if (detected !== 'عام') current = detected;
    splitQuestions(raw).forEach(question => questions.push({
      id: questions.length + 1, topic: topicFor(question, current), question,
      page: pageIndex + 1, solution: '', source: 'تمارين جبر خطي(2).pdf'
    }));
  });
  const result = {source: path.basename(PDF), pageCount: pages.length, questionCount: questions.length, topics: [...new Set(questions.map(q => q.topic))], questions, warning: questions.length ? '' : 'لم يُستخرج نص؛ الملف قد يكون مصوراً ويحتاج OCR.'};
  fs.writeFileSync(OUT, JSON.stringify(result, null, 2), 'utf8');
  console.log(`pages=${result.pageCount} questions=${result.questionCount}`);
  if (!questions.length) console.log(result.warning);
  return result;
}
app.use(express.json());
app.use(express.static(ROOT));
app.get('/api/questions', (req, res) => fs.existsSync(OUT) ? res.sendFile(OUT) : res.status(404).json({error:'شغّل npm run extract أولاً'}));
app.post('/api/extract', async (req, res) => { try { res.json(await extract()); } catch (e) { res.status(500).json({error:e.message}); } });
if (process.argv.includes('--extract')) extract().catch(e => { console.error(e.message); process.exit(1); });
else app.listen(PORT, () => console.log(`http://localhost:${PORT}/index.html`));
