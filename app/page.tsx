'use client';

import { motion } from 'framer-motion';

export default function Home() {
  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 px-6 md:px-20 py-16">

      {/* ================= HERO ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-4xl md:text-5xl font-bold mb-6"
        >
          Hi, I’m Bhaswanth Pacha 👋
        </motion.h1>

        <p className="text-xl text-neutral-300 mb-4">
          Software Development Engineer in Test (SDET)
        </p>

        <p className="text-neutral-400 max-w-3xl mb-8 leading-relaxed">
          SDET with <strong>5+ years of experience</strong> validating large-scale,
          cloud-native and distributed systems. Specialized in building scalable
          automation frameworks, API testing, and embedding quality into CI/CD
          pipelines to deliver reliable, zero-defect releases across enterprise domains.
        </p>

        <div className="flex gap-4">
          <a
            href="mailto:pachabhaswanth@csu.fullerton.edu"
            className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 transition"
          >
            Contact Me
          </a>
          <a
            href="https://www.linkedin.com"
            target="_blank"
            className="px-5 py-2 rounded-xl border border-neutral-700 hover:bg-neutral-800 transition"
          >
            LinkedIn
          </a>
        </div>
      </section>

      {/* ================= ABOUT ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-4">About</h2>
        <p className="text-neutral-400 leading-relaxed">
          I specialize in embedding quality into the software lifecycle by designing
          robust automation frameworks, integrating testing into CI/CD pipelines,
          and collaborating closely with engineering teams to deliver zero-defect releases
          at enterprise scale.
        </p>
      </section>

      {/* ================= WHAT I DO ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-6">What I Do</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {[
            {
              title: 'Automation Frameworks',
              desc: 'Design and scale automation frameworks using Java, Python, Selenium, Playwright, and TestNG.'
            },
            {
              title: 'API & Microservices Testing',
              desc: 'Validate REST APIs and distributed microservices using REST Assured, Postman, and contract testing.'
            },
            {
              title: 'CI/CD Quality Engineering',
              desc: 'Integrate automated testing into Jenkins and GitHub Actions pipelines for faster, safer releases.'
            },
            {
              title: 'Enterprise QA Strategy',
              desc: 'Define test strategies, quality metrics, and traceability for large-scale enterprise systems.'
            }
          ].map(item => (
            <div
              key={item.title}
              className="bg-neutral-900 border border-neutral-800 rounded-xl p-6"
            >
              <h3 className="font-semibold mb-2">{item.title}</h3>
              <p className="text-neutral-400 text-sm">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ================= SKILLS ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-6">Skills</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {[
            'Java, Python, JavaScript, TypeScript',
            'Selenium, Playwright, Cypress, TestNG, JUnit',
            'REST Assured, Postman, API Testing',
            'AWS, Azure, Docker, Kubernetes',
            'Jenkins, GitHub Actions, CI/CD Pipelines',
            'MySQL, PostgreSQL, MongoDB, SQL Optimization',
            'Agile / Scrum, Jira, Test Strategy Design'
          ].map(skill => (
            <div
              key={skill}
              className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 text-neutral-300"
            >
              {skill}
            </div>
          ))}
        </div>
      </section>

      {/* ================= EXPERIENCE ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-6">Experience</h2>

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold">
            IBM — Software Development Engineer in Test
          </h3>
          <p className="text-neutral-400 text-sm mb-4">
            Jan 2019 – Jul 2024 · Bangalore, India
          </p>

          <ul className="list-disc list-inside text-neutral-400 space-y-2 leading-relaxed">
            <li>
              Led automation framework modernization supporting <strong>200+ microservices</strong>,
              reducing manual testing effort by <strong>60%</strong>.
            </li>
            <li>
              Integrated automated tests into Jenkins CI/CD pipelines, improving release
              velocity by <strong>25%</strong>.
            </li>
            <li>
              Automated <strong>80% of 2,000+ test cases</strong>, enabling weekly enterprise releases.
            </li>
            <li>
              Designed API, integration, and performance testing strategies preventing
              <strong> 150+ critical defects</strong> annually.
            </li>
            <li>
              Collaborated with cross-functional Agile teams to consistently deliver
              <strong> zero-defect releases</strong>.
            </li>
          </ul>
        </div>
      </section>

      {/* ================= PROJECTS ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-6">Projects</h2>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
            <h3 className="font-semibold mb-2">TestOpsHub</h3>
            <p className="text-neutral-400 text-sm leading-relaxed">
              Cloud-native automated test execution and reporting platform built using
              Python, FastAPI, React, and Azure. Enabled 500+ concurrent test executions,
              real-time reporting, and reduced end-to-end test cycles by 35%.
            </p>
          </div>

          <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6">
            <h3 className="font-semibold mb-2">Speech Emotion Classification</h3>
            <p className="text-neutral-400 text-sm leading-relaxed">
              Machine learning system using MFCC features and Random Forest to classify
              real-time speech emotions with 95% accuracy.
            </p>
          </div>
        </div>
      </section>

      {/* ================= CERTIFICATIONS ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-6">Certifications & Awards</h2>
        <ul className="list-disc list-inside text-neutral-400 space-y-2">
          <li>IBM Excellence Award – Outstanding Performance in Test Automation</li>
          <li>Microsoft Azure Data Fundamentals</li>
          <li>AHM 250 – Healthcare Management</li>
        </ul>
      </section>

      {/* ================= EDUCATION ================= */}
      <section className="max-w-4xl mx-auto mb-28">
        <h2 className="text-2xl font-semibold mb-6">Education</h2>
        <div className="space-y-4 text-neutral-400">
          <div>
            <p className="font-medium text-neutral-200">
              Master of Science in Computer Science
            </p>
            <p>California State University, Fullerton — Expected May 2026</p>
          </div>
          <div>
            <p className="font-medium text-neutral-200">
              Bachelor of Technology in Information Technology
            </p>
            <p>Sree Vidyanikethan Engineering College — 2018</p>
          </div>
        </div>
      </section>

      {/* ================= FOOTER ================= */}
      <footer className="max-w-4xl mx-auto text-neutral-500 text-sm">
        © {new Date().getFullYear()} Bhaswanth Pacha · San Jose, CA
      </footer>

    </main>
  );
}
