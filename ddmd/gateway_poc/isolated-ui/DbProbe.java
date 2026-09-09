import java.io.*;import java.util.*;import com.ibatis.sqlmap.client.*;import org.springframework.jdbc.datasource.DriverManagerDataSource;import hira.ddmd.jmc.client.dao.ResultDocumentDAO;import hira.ddmd.jmc.client.model.dto.ResultDocument;
public class DbProbe {
 public static void main(String[] a)throws Exception{
  org.apache.log4j.LogManager.resetConfiguration();org.apache.log4j.Logger.getRootLogger().setLevel(org.apache.log4j.Level.OFF);
  DriverManagerDataSource ds=new DriverManagerDataSource();ds.setDriverClassName("org.sqlite.JDBC");ds.setUrl("jdbc:sqlite:"+a[0]+"/data/ddmd_data.db3");
  SqlMapClient sql=SqlMapClientBuilder.buildSqlMapClient(new InputStreamReader(DbProbe.class.getResourceAsStream("/SqlMapConfig.xml"),"UTF-8"));
  ResultDocumentDAO dao=new ResultDocumentDAO();dao.setSqlMapClient(sql);dao.setDataSource(ds);dao.afterPropertiesSet();
  ResultDocument d=new ResultDocument();d.setNtcDocId("ISOLATED-NOTICE-001");d.setYkiho("00000000");d.setDmdTpCd("0");d.setInsuTpCd("Y");d.setNtcTtl("ISOLATED LOCAL NOTICE TEST");d.setNtcStatCd("3");d.setRecpStaDt("2026-09-09 00:00:00");d.setRecpEndDt("2026-09-09 00:00:01");d.setNtcFileLen(762);d.setNtcDocCnt(3);d.setHbrCd("00");d.setAddTtl("");d.setArivDt("2026-09-09 00:00:00");d.setNtcDocCd("TEST");d.setNtcDocNo("ISOLATED");
  dao.insertResultDocument(d);if(dao.getResultDocument(d)==null)throw new Exception("missing row");System.out.println("CHECK originalDaoInsertAndRead=true");
  if(!dao.updateResultDocumentTransState(d,true))throw new Exception("update failed");ResultDocument got=dao.getResultDocument(d);System.out.println("CHECK originalDaoGenerationState="+got.getNtcStatCd());
  Map<String,String> q=new HashMap<String,String>();q.put("fromDt","2026-09-09");q.put("toDt","2026-09-09");q.put("ykiho","00000000");q.put("insuTpCd","Y");if(dao.getResultDocuments(q).size()!=1)throw new Exception("list mismatch");System.out.println("RESULT DB_PASS rows=1");
 }
}
