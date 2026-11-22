-- ============================================================
-- Chuxin Scale Norms Evidence-Based Threshold Updates
-- Generated: 2026-06-21
-- Source: Published normative data from peer-reviewed literature
-- ============================================================

-- ============================================================
-- 1. TIPI — Ten-Item Personality Inventory
-- Ref: Gosling, Rentfrow, & Swann (2003), J Research in Personality
-- Current: all dimensions use 2.5/4.5/5.5 (not evidence-based)
-- Update: dimension-specific M±1SD from Gosling et al. (2003)
-- ============================================================

-- TIPI Dimension 1: 外向性 (Extraversion) M=3.45 SD=1.53
-- Cutoffs: 1.92 / 3.45 / 4.98
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 1.92' WHERE id = 'c5f9b2d8-3eba-4bb3-a7fd-a28380a9f5f6';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 1.92 && hx_wd_y_1 <= 3.45' WHERE id = '715d8137-74a7-4a2e-8f56-b3062163f40f';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 3.45 && hx_wd_y_1 <= 4.98' WHERE id = 'f44cf101-3fc1-49e8-9411-5dbe22957390';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 4.98' WHERE id = '9eac1e21-aa54-4a15-b825-93d43ca32ec7';

-- TIPI Dimension 2: 宜人性 (Agreeableness) M=5.23 SD=1.13
-- Cutoffs: 4.10 / 5.23 / 6.36
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 <= 4.10' WHERE id = 'a67fe402-7091-47a3-9808-f5f173fb1e68';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 4.10 && hx_wd_y_2 <= 5.23' WHERE id = '82eda04e-09ab-4fc3-a511-2c90dd3f6df4';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 5.23 && hx_wd_y_2 <= 6.36' WHERE id = '1937f263-c800-4bb9-8fba-0c2bc442b798';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 6.36' WHERE id = '0d4e96bf-ba4e-49e5-b27a-940b1d1575eb';

-- TIPI Dimension 3: 尽责性 (Conscientiousness) M=5.44 SD=1.25
-- Cutoffs: 4.19 / 5.44 / 6.69
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 <= 4.19' WHERE id = 'cb6f1433-43cc-43c7-8a04-75087233b39e';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 4.19 && hx_wd_y_3 <= 5.44' WHERE id = 'c4c41e36-81e7-42e9-902e-f5901c77855c';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 5.44 && hx_wd_y_3 <= 6.69' WHERE id = '37e4fe92-3b7c-4d8b-929f-59af7e2d9fc0';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 6.69' WHERE id = '93513c49-6191-4661-9ca1-873f107c2ed8';

-- TIPI Dimension 4: 情绪稳定性 (Emotional Stability) M=4.83 SD=1.37
-- Cutoffs: 3.46 / 4.83 / 6.20
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 <= 3.46' WHERE id = '770b13e3-5d4b-42ab-841e-988bd066f0b6';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 3.46 && hx_wd_y_4 <= 4.83' WHERE id = 'd7fd0c86-2e4e-4be9-a0fa-561a4fab96f0';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 4.83 && hx_wd_y_4 <= 6.20' WHERE id = '8fba3437-811c-4182-aa30-ca79050e4049';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 6.20' WHERE id = '2d846590-d339-4291-9a61-12851c3b1315';

-- TIPI Dimension 5: 开放性 (Openness) M=5.55 SD=1.14
-- Cutoffs: 4.41 / 5.55 / 6.69
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 <= 4.41' WHERE id = '4bedfcd4-be64-4e20-aba2-20db27cc1e4e';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 > 4.41 && hx_wd_y_5 <= 5.55' WHERE id = '02f68488-54cb-4a64-889e-e87fd35dcded';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 > 5.55 && hx_wd_y_5 <= 6.69' WHERE id = '958442a8-be90-4bcc-aa47-0183966a0d48';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 > 6.69' WHERE id = '6ecd4967-1974-4f65-a636-853d8450bf71';

-- ============================================================
-- 3. PANAS — Positive and Negative Affect Schedule
-- Ref: Watson, Clark, & Tellegen (1988), JPSP
-- Chinese norms: 黄丽等 (2003), 中国心理卫生杂志
-- PA: M=29.7 SD=7.1; NA: M=22.4 SD=6.6
-- ============================================================

-- PANAS 正性情绪 (PA) Cutoffs: 22.6 / 29.7 / 36.8
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 22.6' WHERE id = 'f4f36a0a-ae25-42e1-80f0-344f07a37172';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 22.6 && hx_wd_y_1 <= 29.7' WHERE id = '51bc7c0f-9387-4d86-9675-37648803b6b8';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 29.7 && hx_wd_y_1 <= 36.8' WHERE id = 'b14d0b9c-885f-4b21-8e82-112db50aed2a';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 36.8' WHERE id = '08a81b10-0261-4c04-8911-f17bc5b6a98f';

-- PANAS 负性情绪 (NA) Cutoffs: 15.8 / 22.4 / 29.0
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 <= 15.8' WHERE id = '82337e58-63ee-457e-8180-bdea45446353';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 15.8 && hx_wd_y_2 <= 22.4' WHERE id = 'a215ae70-db3a-4a2f-af63-d7ffecaba738';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 22.4 && hx_wd_y_2 <= 29.0' WHERE id = 'd9fef0ad-e367-43d6-a1d9-c94607fa181b';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 29.0' WHERE id = '50a8eea5-4a3c-402f-81fd-5162e8d4c9fe';

-- ============================================================
-- 4. BPAQ — Buss-Perry Aggression Questionnaire
-- Ref: Buss & Perry (1992), JPSP
-- Physical M=21.3 SD=8.5; Verbal M=15.3 SD=4.6
-- Anger M=17.0 SD=6.6; Hostility M=21.1 SD=7.7; Total M=74.8 SD=19.7
-- ============================================================

-- BPAQ 身体攻击性 Cutoffs: 12.8 / 21.3 / 29.8
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 12.8' WHERE id = 'fc35231f-9846-476b-9cdc-c4683cd0f56b';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 12.8 && hx_wd_y_1 <= 21.3' WHERE id = '77fdb75c-7e22-4600-8de8-877bd7685ee3';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 21.3 && hx_wd_y_1 <= 29.8' WHERE id = '4955a14f-f457-4b0f-87d9-aa87326f26c5';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 29.8' WHERE id = '1628f08a-cad8-4afb-ae97-3062de80ead9';

-- BPAQ 言语攻击性 Cutoffs: 10.7 / 15.3 / 19.9
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 <= 10.7' WHERE id = 'c24df297-95a2-477b-9831-f34ed7a4bad3';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 10.7 && hx_wd_y_2 <= 15.3' WHERE id = '4a275b1a-438e-4ed0-a19f-42d231618c7a';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 15.3 && hx_wd_y_2 <= 19.9' WHERE id = 'ade9363f-bd70-451a-8f9e-b397077ece4b';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 19.9' WHERE id = '27a3e7ec-6a11-4aac-b0ed-a47c3875d790';

-- BPAQ 愤怒 Cutoffs: 10.4 / 17.0 / 23.6
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 <= 10.4' WHERE id = 'a48858e3-ec4d-48be-99ad-294265a26bed';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 10.4 && hx_wd_y_3 <= 17.0' WHERE id = 'b906cc80-1ec8-43eb-bc96-335b6ddfd67e';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 17.0 && hx_wd_y_3 <= 23.6' WHERE id = 'fbe7bb3f-4e9a-464d-ae3f-9d94da59f86d';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 23.6' WHERE id = '47773529-7197-489c-af90-a411655371ef';

-- BPAQ 敌意 Cutoffs: 13.4 / 21.1 / 28.8
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 <= 13.4' WHERE id = '15e66aeb-ae68-472c-b068-263687db7e85';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 13.4 && hx_wd_y_4 <= 21.1' WHERE id = '6deba92a-7f98-4f56-bcc2-35310ab09a5f';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 21.1 && hx_wd_y_4 <= 28.8' WHERE id = '1d3127f9-b91b-493b-af75-6904886186a6';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 28.8' WHERE id = 'e9b60107-b0c9-4eae-8623-e170a55b9903';

-- BPAQ 攻击性总分 Cutoffs: 55.1 / 74.8 / 94.5
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 <= 55.1' WHERE id = '2860b918-a80e-400d-a0ab-f3910efe31ec';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 > 55.1 && hx_wd_y_5 <= 74.8' WHERE id = 'ec6b78b2-6596-41e7-9bdd-d27112f500d2';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 > 74.8 && hx_wd_y_5 <= 94.5' WHERE id = 'bc2c2fcc-1b82-4374-b60c-8b04c4bccb28';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_5 > 94.5' WHERE id = 'bf4124f6-b715-43cc-aa08-7e246749eef6';

-- ============================================================
-- 5. BIS-11 — Barratt Impulsiveness Scale
-- Ref: Patton, Stanford, & Barratt (1995), J Clinical Psychology
-- Attention M=18.6 SD=4.6; Motor M=22.1 SD=5.2
-- Total M=64.3 SD=12.7
-- ============================================================

-- BIS-11 注意力冲动性 Cutoffs: 14.0 / 18.6 / 23.2
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 14' WHERE id = 'c761a0c7-189b-42f4-9af8-d874167e920d';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 14 && hx_wd_y_1 <= 19' WHERE id = '33bcbc01-5fef-42e4-9c7a-9902d6400387';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 19 && hx_wd_y_1 <= 23' WHERE id = '96d1b533-ba51-4654-b954-99746c7ad52f';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 23' WHERE id = 'da71f124-1d1c-4b73-bbd5-abcc98f619ea';

-- BIS-11 运动冲动性 Cutoffs: 16.9 / 22.1 / 27.3
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 <= 17' WHERE id = 'e8a849df-bd4b-47cf-bfd8-a410a6ad7b23';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 17 && hx_wd_y_2 <= 22' WHERE id = 'f0ae3025-32e1-436e-beaa-a91f11ae622d';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 22 && hx_wd_y_2 <= 27' WHERE id = '59d17fd0-876c-419f-bab7-fd730980ccf7';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 27' WHERE id = '9804cf8d-303a-49ac-94ee-6d35283dfacb';

-- BIS-11 冲动性总分 Cutoffs: 51.6 / 64.3 / 77.0
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 <= 52' WHERE id = 'e0b7d32f-ee42-488c-8b41-52929e96f82d';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 52 && hx_wd_y_4 <= 64' WHERE id = '55f3ef0f-f91c-4ba5-8ad2-4c6ce559fcdc';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 64 && hx_wd_y_4 <= 77' WHERE id = 'ccb5f691-d660-4bcc-b373-31f396a529d0';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_4 > 77' WHERE id = '77ca50a4-166f-4ff5-897e-4f4e3569e845';

-- ============================================================
-- 6. LSRP — Levenson Self-Report Psychopathy Scale
-- Ref: Levenson, Kiehl, & Fitzpatrick (1995), JPSP
-- Community norms (Brinkley et al., 2008):
-- Primary M=31.2 SD=7.8; Secondary M=20.8 SD=5.2
-- ============================================================

-- LSRP 原发性精神病态 Cutoffs: 23.4 / 31.2 / 39.0
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 23' WHERE id = 'ffaf9b30-c46f-433a-88c2-c596f01bd71e';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 23 && hx_wd_y_1 <= 31' WHERE id = '8cc10fe2-23b8-4e8d-8464-f88c06ec06dd';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 31 && hx_wd_y_1 <= 39' WHERE id = 'fecf721d-566c-4663-b700-dcb775dc4bd0';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 39' WHERE id = '0df99023-89f5-4eee-8eb4-e77a04d082fc';

-- LSRP 继发性精神病态 Cutoffs: 15.6 / 20.8 / 26.0
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 <= 16' WHERE id = '79bcf79f-8735-4e12-9155-25ec3ecceccc';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 16 && hx_wd_y_2 <= 21' WHERE id = 'e86dd686-cf3d-41ea-9cc0-db7f3ed595a3';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 21 && hx_wd_y_2 <= 26' WHERE id = '812569ef-4783-44fd-bc18-488ed22d342a';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_2 > 26' WHERE id = 'eb273133-97f5-4a4a-aebc-3d72d6da451f';

-- ============================================================
-- 7. HSNS — Hypersensitive Narcissism Scale
-- Ref: Hendin & Cheek (1997), J Research in Personality
-- M=29.4 SD=7.4 (US college sample, N=504)
-- Cutoffs: 22.0 / 29.4 / 36.8
-- ============================================================

UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 22' WHERE id = 'ceda0081-7cb6-49bd-910f-737a14195ca5';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 22 && hx_wd_y_1 <= 29' WHERE id = 'adb0d0ae-aa0a-4362-907a-c3ede62f8815';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 29 && hx_wd_y_1 <= 37' WHERE id = '9af90ee8-592a-4f82-adc8-dfc560dc8cd7';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 37' WHERE id = '5d33093b-d444-4bd3-80b7-6120c314535b';

-- ============================================================
-- 8. NPI-16 — Narcissistic Personality Inventory (16-item)
-- Ref: Ames, Rose, & Anderson (2006), J Research in Personality
-- M=0.37 SD=0.17 (proportion, US college)
-- Cutoffs: 0.20 / 0.37 / 0.54
-- ============================================================

UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 0.20' WHERE id = '3c9b98eb-ac36-413e-a6c2-3767d8991549';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 0.20 && hx_wd_y_1 <= 0.37' WHERE id = '7541e027-0c84-477d-9eb6-bac09f9f18a9';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 0.37 && hx_wd_y_1 <= 0.54' WHERE id = 'dc3f448b-2f96-4ee0-9517-6d9731d324b4';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 0.54' WHERE id = 'f2ce946b-f2b5-4c7a-af45-243c2d5e59f4';

-- ============================================================
-- 9. EQ — Emotional Intelligence Scale (Schutte)
-- Ref: Schutte et al. (1998), Personality & Individual Differences
-- Combined: M=128 SD=15.5
-- 4-tier cutoffs: 112.5 / 128 / 143.5
-- ============================================================

UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 112' WHERE id = '8a69718f-c4f6-488b-827f-a441dac65b2b';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 112 && hx_wd_y_1 <= 128' WHERE id = '03d404d2-5c7e-420a-8e73-e8f0783ef285';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 128 && hx_wd_y_1 <= 144' WHERE id = '1e2786e1-8e85-4a47-a333-54f70a23832a';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 144 && hx_wd_y_1 <= 160' WHERE id = '6409ccfd-4a1e-4a40-853c-fefc26f36140';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 160' WHERE id = '2eea0e20-ce6a-4216-a25a-33c4cf984036';

-- ============================================================
-- 10. FS — Flourishing Scale
-- Ref: Diener et al. (2010), Social Indicators Research
-- M=44.0 SD=7.0 (US sample)
-- 4-tier cutoffs: 37.0 / 40.5 / 47.5 / 51.0
-- ============================================================

UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 37' WHERE id = 'bedd8b42-2f08-417d-a626-2cb2ea4f2d27';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 37 && hx_wd_y_1 <= 41' WHERE id = 'd0d74131-0238-40cd-9121-0744e3eb8237';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 41 && hx_wd_y_1 <= 48' WHERE id = '1b0ce6dc-2580-407f-a6f8-e46939b111f0';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 48' WHERE id = '2701425c-f3dc-4237-95de-f29a77ed26c7';

-- ============================================================
-- 11. RRS — Ruminative Responses Scale
-- Ref: Nolen-Hoeksema & Morrow (1991), JPSP
-- M=42.0 SD=12.0 (women)
-- 4-tier cutoffs: 30.0 / 36.0 / 48.0 / 54.0
-- ============================================================

UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 30' WHERE id = '4ff2c02f-9ac6-46fc-9e32-4f354f99fd2b';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 30 && hx_wd_y_1 <= 36' WHERE id = '3e19f0a9-5536-4015-bb5a-49666fbcb91c';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 36 && hx_wd_y_1 <= 48' WHERE id = '61093f3c-9a35-4815-b2a0-9b89cb77e52e';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 48' WHERE id = 'aac81f79-2357-4157-a2c1-88528150db7d';

-- ============================================================
-- 13. CFQ — Cognitive Failures Questionnaire
-- Ref: Broadbent et al. (1982), British J Clinical Psychology
-- M=43.0 SD=14.0
-- 4-tier cutoffs: 29.0 / 36.0 / 50.0 / 57.0
-- ============================================================

UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 <= 29' WHERE id = 'a9775e8f-7ee6-4934-887c-eb62715db9d7';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 29 && hx_wd_y_1 <= 36' WHERE id = '7af60485-c60b-42c8-ac48-6b6cc5f88921';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 36 && hx_wd_y_1 <= 50' WHERE id = '9e5bc635-e843-4e7d-8b52-74ebfe73acc0';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_1 > 50' WHERE id = '3681466a-a3bb-443a-a86b-5b4ae17809f3';

-- ============================================================
-- 24. LOT-R — Life Orientation Test-Revised
-- Ref: Scheier, Carver, & Bridges (1994), JPSP
-- Total M=14.3 SD=4.3
-- ============================================================

-- LOT-R 总分 Cutoffs: 10.0 / 14.3 / 18.6
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 <= 10' WHERE id = '290bfc7b-f58a-498b-9340-be50500d4322';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 10 && hx_wd_y_3 <= 14' WHERE id = '06c70454-cccb-4b51-a984-cfa2dbce71c5';
UPDATE scale_result_definitions SET condition_expression = 'hx_wd_y_3 > 14 && hx_wd_y_3 <= 19' WHERE id = 'b9a4c542-2864-493d-aa33-904f519b8ead';

-- ============================================================
-- END OF UPDATES
-- Scales NOT modified (already evidence-based or no change needed):
-- - GRIT-S: current cutoffs (2.5/3.4/4.2) close to M±SD (2.7/3.4/4.1)
-- - OCI-R: clinical cutoff ≥21 is correct
-- - BIS-11 非计划冲动性: keep current (10-item version norms uncertain)
-- - WebEXEC: limited published norms
-- - CWB-C: midpoint-based cutoffs reasonable
-- - OJS: midpoint-based cutoffs reasonable
-- - MDS: midpoint-based cutoffs reasonable
-- - ELS: midpoint-based cutoffs reasonable
-- - VAST: gender-dependent norms, current thresholds use combined
-- - WDS: midpoint-based cutoffs reasonable
-- - LiES: limited normative data available
-- - BFS: limited normative data available
-- - NCS-6: midpoint-based cutoffs reasonable
-- ============================================================
